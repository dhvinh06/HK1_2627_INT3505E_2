"""Lab 4: local Books API traffic, owned fixtures and synthetic search failures.

Run from Week8; see README for scenarios. Synthetic failures never change the
server's status: every 100th valid search is marked failed in Locust, explicitly
as SYNTHETIC_HTTP_500. Short runs with fewer than 100 valid searches inject none.
"""
import itertools
import json
import random
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import urlsplit
from uuid import uuid4

from locust import HttpUser, between, events, task

_searches = itertools.count(1)
_diagnostics = defaultdict(Counter)
_pending = set()
SYNTHETIC_ERROR = "SYNTHETIC_HTTP_500: Locust simulation; server returned HTTP 200"


def require_local_host(value):
    host = urlsplit(value or "")
    if host.scheme != "http" or host.hostname not in ("127.0.0.1", "localhost") or host.port != 5000:
        raise ValueError("Lab 4 only targets http://127.0.0.1:5000 or http://localhost:5000")


@events.test_start.add_listener
def start_test(environment, **kwargs):
    """Reset deterministic injection/workload seed for each standalone run."""
    global _searches
    require_local_host(environment.host)
    _searches = itertools.count(1)
    _diagnostics.clear()
    _pending.clear()
    random.seed(20261118)


def simulate_search_failure():
    """Exactly floor(N/100) injections among N valid searches per process."""
    return next(_searches) % 100 == 0


@events.request.add_listener
def record_response(name, response=None, exception=None, **kwargs):
    """Keep actual HTTP statuses separate from client-side classifications."""
    status = getattr(response, "status_code", 0)
    counts = _diagnostics[name]
    counts[f"http_{status}"] += 1
    if exception is not None:
        if str(exception) == SYNTHETIC_ERROR:
            counts["synthetic_failures"] += 1
        elif status >= 500:
            counts["server_failures"] += 1
        elif not status:
            counts["transport_failures"] += 1
        else:
            counts["contract_failures"] += 1
    elif status == 404:
        counts["expected_not_found"] += 1


@events.quitting.add_listener
def save_diagnostics(environment, **kwargs):
    """Supplement Locust's real HTML/CSV reports with measured classifications."""
    html_file = getattr(environment.parsed_options, "html_file", None)
    if html_file:
        target = Path(html_file).with_name(Path(html_file).stem + "_diagnostics.json")
        target.parent.mkdir(parents=True, exist_ok=True)
        def snapshot(stats):
            return {
                "requests": stats.num_requests,
                "failures": stats.num_failures,
                "failure_rate_percent": stats.fail_ratio * 100,
                "average_ms": stats.avg_response_time,
                "p50_ms": stats.get_response_time_percentile(0.5),
                "p95_ms": stats.get_response_time_percentile(0.95),
                "p99_ms": stats.get_response_time_percentile(0.99),
                "rps": stats.total_rps,
            }
        target.write_text(json.dumps({
            "endpoints": dict(_diagnostics),
            "remaining_owned_ids": sorted(_pending),
            "simulation": "Every 100th valid search; real HTTP status remains 200",
            # Locust's periodic CSV may precede shutdown cleanup. These final
            # values come directly from Locust's in-memory statistics after it.
            "aggregate": snapshot(environment.stats.total),
            "endpoint_stats": {entry.name: snapshot(entry) for entry in environment.stats.entries.values()},
        }, indent=2) + "\n", encoding="utf-8")


def validate_book(book):
    if not isinstance(book, dict) or set(book) != {"id", "title", "author", "year", "isbn"}:
        raise ValueError("Invalid Book structure")
    if type(book["id"]) is not int or book["id"] < 1:
        raise ValueError("Invalid Book id")
    if any(not isinstance(book[key], str) or not book[key] for key in ("title", "author")):
        raise ValueError("Invalid Book title/author")
    if book["year"] is not None and type(book["year"]) is not int:
        raise ValueError("Invalid Book year")
    if book["isbn"] is not None and (not isinstance(book["isbn"], str)
                                       or len(book["isbn"]) != 13 or not book["isbn"].isdigit()):
        raise ValueError("Invalid Book ISBN")


def check_status(response, expected):
    if response.status_code == expected:
        return True
    if not response.status_code:
        response.failure(f"TRANSPORT_ERROR: {response.error}")
    else:
        response.failure(f"SERVER_HTTP_{response.status_code}: expected {expected}")
    return False


class BooksUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        require_local_host(self.host)  # Check before this user can send any HTTP request.
        self.client.trust_env = False  # Local-only traffic must not use system proxies.
        self.owned_ids = set()
        self.book_id = self._create("POST /books (setup)")

    def on_stop(self):
        for book_id in list(self.owned_ids):
            self._delete(book_id, "DELETE /books/{id} (cleanup)")

    @task(3)
    def list_books(self):
        self._list("GET /books")

    def _list(self, name, year=None):
        with self.client.get("/books", params={} if year is None else {"year": year},
                             name=name, catch_response=True, timeout=5) as response:
            if not check_status(response, 200):
                return
            try:
                books = response.json()
                if not isinstance(books, list):
                    raise ValueError("Expected a JSON array")
                for book in books:
                    validate_book(book)
                    if year is not None and book["year"] != year:
                        raise ValueError("Year filter returned a nonmatching book")
            except ValueError as exc:
                response.failure(f"CONTRACT_ERROR: {exc}")
                return
            # Inject only after checking a genuine successful server response.
            # Real HTTP errors, timeouts and invalid JSON are never masked.
            if year is not None and simulate_search_failure():
                response.failure(SYNTHETIC_ERROR)

    @task(2)
    def read_book(self):
        if self.book_id is None:
            self.list_books()
            return
        with self.client.get(
            f"/books/{self.book_id}", name="GET /books/{id}", catch_response=True, timeout=5
        ) as response:
            try:
                if response.status_code == 404:
                    if response.json().get("code") != "NOT_FOUND":
                        raise ValueError("Invalid NOT_FOUND contract")
                    response.success()  # A concurrently removed resource is a business outcome.
                    self.book_id = None
                elif check_status(response, 200):
                    book = response.json()
                    validate_book(book)
                    if book["id"] != self.book_id:
                        raise ValueError("Read returned the wrong book id")
            except (ValueError, AttributeError) as exc:
                response.failure(f"CONTRACT_ERROR: {exc}")

    @task(1)
    def create_book(self):
        book_id = self._create("POST /books")
        if book_id is not None:
            self._delete(book_id, "DELETE /books/{id}")

    def _create(self, name):
        payload = {"title": f"Locust {uuid4().hex}", "author": "locust-lab4", "year": 2017}
        with self.client.post("/books", json=payload, name=name,
                              catch_response=True, timeout=5) as response:
            if not check_status(response, 201):
                return None
            try:
                book = response.json()
                validate_book(book)
                if any(book[key] != value for key, value in payload.items()):
                    raise ValueError("Created book does not match submitted data")
                self.owned_ids.add(book["id"])
                _pending.add(book["id"])
                return book["id"]
            except ValueError as exc:
                response.failure(f"CONTRACT_ERROR: {exc}")
        return None

    def _delete(self, book_id, name):
        # Only delete ids returned by this user's own successful creates.
        if book_id not in self.owned_ids:
            return
        with self.client.delete(f"/books/{book_id}", name=name,
                                catch_response=True, timeout=5) as response:
            if response.status_code == 404:
                try:
                    if response.json().get("code") != "NOT_FOUND":
                        raise ValueError("Invalid NOT_FOUND contract")
                except (ValueError, AttributeError) as exc:
                    response.failure(f"CONTRACT_ERROR: {exc}")
                    return
                response.success()
            elif not check_status(response, 204):
                return
            elif response.content:
                response.failure("CONTRACT_ERROR: DELETE 204 must have no body")
                return
            self.owned_ids.discard(book_id)
            _pending.discard(book_id)

    @task(2)
    def search_by_year(self, year=2017):
        self._list("GET /books?year={year}", year=year)
