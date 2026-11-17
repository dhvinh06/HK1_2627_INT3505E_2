# lab08-starter — API Testing & Quality Assurance

**Flask 3.x / SQLAlchemy / pytest / OpenAPI / Postman / Locust**

## 1. Chuẩn bị và chạy API

Yêu cầu: Python **3.11+**; Node.js **18+** nếu chạy Newman/Spectral. Chạy từ thư mục gốc project.

```bash
python -m venv .venv
# Linux/macOS:
source .venv/bin/activate
# Windows PowerShell:
# .venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m app --port 5000
```

API: `http://127.0.0.1:5000` (chỉ chạy trên máy local). Thử:

```bash
curl http://127.0.0.1:5000/health
curl http://127.0.0.1:5000/books
curl -X POST http://127.0.0.1:5000/books \
  -H 'Content-Type: application/json' \
  -d '{"title":"API Design Patterns","author":"J.J. Geewax","year":2021}'
```

SQLite lưu tại `instance/books.db` (không commit lên Git). API không có authentication bắt buộc cho CRUD để dễ thực hành functional test. `POST /auth/login` chỉ là **mô phỏng cục bộ**, tài khoản `lab/lab`; token không cấp quyền và **không được dùng trong production**.

### REST endpoints

| Method | Path | Trả về |
|---|---|---|
| GET | `/health` | 200 |
| GET | `/books?author=&year=&page=` | 200, JSON array, page 1-based, 20 items/page |
| GET | `/books/{id}` | 200 / 400 (ID sai định dạng) / 404 |
| POST | `/books` | 201 / 400 / 409 (ISBN trùng) |
| PUT | `/books/{id}` | 200 / 400 / 404 / 409 |
| DELETE | `/books/{id}` | 204 (không body) / 400 / 404 |
| POST | `/auth/login` | 200 / 401, chỉ để minh họa |

Schema JSON của Book trả `id`, `title`, `author`, `year`, `isbn`. Trong request, `title` và `author` là required. `year`/`isbn` tùy chọn; ISBN nếu có là 13 chữ số và unique. **POST lặp lại chỉ 409 nếu xảy ra xung đột ISBN**, không phải vì lặp payload nói chung. DELETE lần đầu 204, lần sau 404; điều này không mâu thuẫn với idempotency vì trạng thái tài nguyên sau hai lần là như nhau.

## 2. Lab 1 — pytest

```bash
python -m pytest -v
```

Hai smoke test có sẵn nhằm xác nhận starter hoạt động. Hãy viết **4 test bắt buộc + 1 bonus** trong `tests/test_lab01.py`, theo các TODO trong file. Fixture `app`, `client`, `sample_book` ở `tests/conftest.py`; dùng `get_book_schema()` từ `tools.py` khi cần. Mỗi test có DB riêng, không phụ thuộc thứ tự. Lưu ý: schema Book trong `openapi.yaml` **đang cố ý sai ở trường year** cho Lab 2; muốn validate response mẫu có `year`, cần hoàn thành sửa lỗi đó trước.

## 3. Lab 2 — OpenAPI/Spectral

Ba lỗi **cố ý** trong `openapi.yaml`:

1. `GET /books` thiếu `operationId`.
2. Response `DELETE /books/{id}` HTTP 204 có `content` dù không được có response body.
3. `Book.year` khai báo `type: string` thay vì kiểu của model Python.

```bash
npm install -g @stoplight/spectral-cli
spectral lint openapi.yaml --ruleset .spectral.yml
```

`.spectral.yml` đã có hai rule riêng kiểm tra (2) và (3); `spectral:oas` kiểm tra các quy tắc nền, bao gồm operationId. Hãy sửa 3 lỗi trong spec và **tự bổ sung custom rule** kiểm tra response 200 có schema không rỗng. Lưu ý: Spectral linter không tự đối chiếu code Flask; một spec hợp lệ vẫn có thể khác hành vi thực tế. Hãy dùng pytest + jsonschema để kiểm chứng response.

## 4. Lab 3 - Postman/Newman

Lab 3 is implemented in `books-api.postman_collection.json`. The existing copy
at `postman/books-api.postman_collection.json` contains the same checks. Use the
root collection for the commands below; no Postman desktop application is needed.
Configuration stays in the existing `postman/local.postman_environment.json`:
`base_url=http://127.0.0.1:5000`. Change that value if the API uses another port.
`book_id` is collection execution state, not an environment setting.

### Start the API (Windows PowerShell, terminal 1)

Requirements: Python 3.11+ and the Flask dependencies in `requirements.txt`;
Node.js 18+ with npm, and Newman. Run all commands **inside `Week8`**.
If needed, create the environment with `python -m venv .venv`, then:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
New-Item -ItemType Directory -Force instance | Out-Null
.\.venv\Scripts\python.exe -m app --port 5000
```

If you already installed these dependencies in the project's parent `.venv`,
reuse it by replacing `.\.venv\Scripts\python.exe` above with
`..\.venv\Scripts\python.exe`; no second Python environment is required.

The existing application uses SQLite at `instance/books.db`. Keep this terminal
running. In terminal 2 (also inside `Week8`), check readiness:

```powershell
Invoke-RestMethod http://127.0.0.1:5000/health
```

### Run the collection and generate JUnit (terminal 2)

Install the verified Newman version locally (no administrator privileges or
global npm configuration changes). The cache and dependencies stay in `Week8`:

```powershell
npm.cmd install --prefix . --no-save --package-lock=false --ignore-scripts --no-audit --no-fund --cache .npm-cache --fetch-retries=0 --fetch-timeout=15000 newman@6.2.3
```

Run all seven requests and write a real JUnit report to `junit.xml`:

```powershell
# Keep local API traffic direct if this terminal uses an HTTP proxy.
$env:NO_PROXY = '127.0.0.1,localhost,' + $env:NO_PROXY
.\node_modules\.bin\newman.cmd run books-api.postman_collection.json `
  -e postman/local.postman_environment.json `
  -r cli,junit `
  --reporter-junit-export junit.xml
$LASTEXITCODE
```

If Newman is already available on PATH, the equivalent command is:

```powershell
newman.cmd run books-api.postman_collection.json -e postman/local.postman_environment.json -r cli,junit --reporter-junit-export junit.xml
$LASTEXITCODE
```

Execution order and expected status codes:

| Folder | Request | Status |
|---|---|---|
| books | GET /books | 200 |
| books | POST /books | 201 |
| books | GET /books/{{book_id}} | 200 |
| books | PUT /books/{{book_id}} | 200 |
| books | DELETE /books/{{book_id}} | 204, empty body |
| error-cases | POST /books without title | 400, VALIDATION_ERROR, title in errors |
| error-cases | GET /books/9999 | 404, NOT_FOUND |

Every request has at least two `pm.test()` blocks (17 total). POST clears stale
`book_id`, then saves a positive integer id from a successful create response;
GET/PUT/DELETE use that id. The book is deleted at the end of the happy path.
No ISBN is submitted, avoiding unique-ISBN conflicts even after interrupted runs.
The fixed not-found example requires that book 9999 does not exist in the local
database. If it does exist, this check correctly fails; use a separate development
database rather than deleting unrelated data.

Success means Newman exits **0**, reports **7 requests**, **17 passed assertions**,
**0 failed assertions**, and writes **17 JUnit testcases** (one per `pm.test`).
The CLI summary reports the collection duration; the local target is under 10 seconds.
A failed assertion, request or script error produces a nonzero exit code. Inspect
the CLI failure details and the JUnit `<failure>`/`<error>` elements; do not use
`--suppress-exit-code`. A connection error usually means the API is not running or
`base_url` has the wrong host/port. The report is generated output, not test input.

Check JUnit counts in PowerShell:

```powershell
[xml]$report = Get-Content -Raw junit.xml
$cases = @($report.SelectNodes('//testcase'))
$failures = @($report.SelectNodes('//testcase/failure | //testcase/error'))
"Testcases: $($cases.Count); failures/errors: $($failures.Count)"
```

`data.csv` remains available for optional data-driven exercises (`-d data.csv`),
which execute the collection once per row. Earlier pytest, OpenAPI and Locust
exercises remain separate from this collection.

### Verified results (2026-11-18, Vietnam time)

Static validation passed for both matching collection JSON files: seven requests
in the required order, 17 `pm.test()` blocks (at least two per request), valid
JavaScript syntax and JSON bodies, and the existing local environment resolving
`base_url`.

The existing API was started from `Week8` with
`..\.venv\Scripts\python.exe -B -m app --port 5000`; `/health` returned
`{"status":"ok"}`. The local `Week8/.venv` lacked Flask, so the documented
parent-environment option was used without changing the backend.

| Check | Actual result |
|---|---|
| Runtime | Node.js 24.15.0, npm 11.12.1, Newman 6.2.3 |
| Requests | 7 executed, 0 failed |
| Assertions | 17 passed, 0 failed |
| Newman exit code | 0 |
| Collection duration (Newman CLI) | 651 ms |
| Process wall time, including CLI startup | 1791 ms |
| JUnit | 17 actual `testcase` elements across 7 request suites, 0 failures/errors |
| Under 10 seconds | PASS |
| Existing pytest regression suite | 6 passed, 0 failed in 0.51 seconds |

`junit.xml` was generated by Newman's JUnit reporter. The actual CLI output is
saved in `reports/lab3-newman.log`. Count `//testcase` elements as shown above:
this Newman reporter's root `tests` attribute is 7 (request suites), while the
file contains 17 assertion testcases.

The earlier install log recorded a registry-fetch failure:
`FetchError: request to https://registry.npmjs.org/newman failed`,
`code: EACCES`, `errno: EACCES`. It did not record a failed cache or global-prefix
write. A local cache write probe succeeded, and the local installation above
subsequently succeeded through the environment's configured proxy (148 packages,
27 seconds). The retained old log does not identify the originating Windows
access-control rule; administrator privileges were not needed to resolve it.

`.gitignore` excludes local npm dependencies/cache, Python environments/cache,
pytest temporary directories and the local SQLite database. These reusable
directories are left in place; the real JUnit report and CLI log are not ignored.

## 5. Lab 4 - Locust

Keep using the existing `performance/locustfile.py` and `performance/analysis.md`;
there are no duplicate root implementations. The optional stateful demo in
`performance/locustfile_realistic.py` is unchanged.

Run from **Week8**, selecting an environment with the dependencies installed:

```powershell
$pythonExe = '..\.venv\Scripts\python.exe'
# Alternatively: '.\.venv\Scripts\python.exe'
& $pythonExe -m pip install -r requirements.txt
```

Locust is already included in `requirements.txt`. Start the existing API in
terminal 1:

```powershell
New-Item -ItemType Directory -Force instance | Out-Null
& $pythonExe -B -m app --port 5000
```

In terminal 2, set `$pythonExe` again, then run **sequentially**:

```powershell
& $pythonExe -B -m locust -f performance/locustfile.py --headless -u 10 -r 2 -t 30s --host http://127.0.0.1:5000 --stop-timeout 10 --html reports/A.html --csv reports/A
& $pythonExe -B -m locust -f performance/locustfile.py --headless -u 50 -r 5 -t 60s --host http://127.0.0.1:5000 --stop-timeout 10 --html reports/B.html --csv reports/B
& $pythonExe -B -m locust -f performance/locustfile.py --headless -u 200 -r 50 -t 30s --host http://127.0.0.1:5000 --stop-timeout 10 --html reports/C.html --csv reports/C
```

Archive existing partial `reports/A*` outputs before retrying A. Never replace
an earlier legitimate report without preserving it. `--stop-timeout 10` allows
in-flight work and cleanup after the requested active duration.

Alternatively, `performance/run_load_tests.py` manages API startup/readiness,
a 5-user/6-second preflight, A/B/C in sequence, and API shutdown. It refuses to
overwrite existing outputs. Its API child blocks external Python socket/DNS
access before importing the unchanged app. Stop any existing API on port 5000
and preserve/archive previous run outputs first:

```powershell
& $pythonExe -B performance/run_load_tests.py
```

**Execution status:** preflight completed successfully. A started but was
interrupted when automatic approval review rejected a connection to an external
telemetry host with an unknown payload, despite the API child's network guard.
B and C were not started. No official A/B/C HTML report was produced. This
execution environment remains blocked; no further server startup was attempted.
The initial `smoke.*` connection-failure outputs and the successful `preflight.*`
outputs are preserved separately. See `performance/analysis.md` for actual data.

Tasks are list/read/search/create with weights **3/2/2/1** and waits of **1-3 s**.
Each user creates and reads its own seed book and deletes it on stop. The create
task uses a UUID title, omits unique ISBN and deletes its new book. Setup/cleanup
have separate request names and are included in aggregate statistics. Abrupt
process termination can prevent cleanup; inspect pending ids/database ownership
before removing interrupted-run test data. Unrelated books are never deleted.

`search_by_year(year=2017)` uses the existing `GET /books?year=2017` filter.
After validating a genuine HTTP 200 response, every 100th valid search per process
is marked `SYNTHETIC_HTTP_500` with `response.failure()`. The server still returned
200. Among N valid searches there are exactly floor(N/100) injections; fewer than
100 valid searches inject none. The failure percentage among *all* requests is
lower because list/read/create/setup/cleanup also run. Real HTTP failures,
timeouts and invalid JSON are checked before injection and never masked.

A run containing synthetic failures normally exits **1**; do not suppress it.
Inspect `*_failures.csv` and `*_diagnostics.json` to separate synthetic failures,
actual server errors, transport failures and contract failures. Valid
`404`/`NOT_FOUND` responses are expected business outcomes and counted separately.

Reports are genuine Locust HTML (`reports/A.html`, `B.html`, `C.html` after
successful completion), periodic `*_stats.csv`/`*_stats_history.csv`, and failure
CSV files. At shutdown the load file exports final Locust in-memory aggregate
and endpoint statistics in `*_diagnostics.json`, including remaining owned ids.
The managed launcher also records commands/process exit codes in
`reports/run_summary.json` and server output in `reports/lab4-api.log`.

CSV snapshots can predate final cleanup; use final HTML/diagnostics for totals.
**p95/p99** bound approximately 95%/99% of measured response times; Locust rounds
percentiles. **RPS** is requests per second; **failure rate** is failed/total
requests, including explicit synthetic failures. Compare aggregate p95 with
**300 ms**, then inspect endpoint rows. Local Flask development server + SQLite
measurements do not establish production capacity.

## 6. Cấu trúc thư mục

```text
lab08-starter/
├── app.py, models.py, tools.py
├── openapi.yaml, .spectral.yml
├── books-api.postman_collection.json
├── data.csv, requirements.txt, pytest.ini
├── tests/
│   ├── conftest.py
│   ├── test_smoke.py             # supplied baseline
│   └── test_lab01.py             # student TODO
├── postman/
│   ├── books-api.postman_collection.json
│   └── local.postman_environment.json
├── performance/
│   ├── locustfile.py
│   ├── locustfile_realistic.py
│   └── analysis.md
├── reports/
└── .github/workflows/tests.yml
```

## Lưu ý:

- OpenAPI cố ý chứa lỗi nên các công cụ contract check phải fail **trước khi sửa**.
- `pytest` và Newman đều chạy được độc lập sau khi đã cài dependency, không cần Postman GUI.
