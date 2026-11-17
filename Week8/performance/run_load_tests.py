r"""Run the existing local API and Lab 4 smoke/A/B/C tests, preserving reports.

From Week8: ..\.venv\Scripts\python.exe -B performance/run_load_tests.py
The API child denies non-loopback network access before importing the app.
This changes no Flask endpoint or application configuration.
"""
import ipaddress
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"


def loopback_only(event, args):
    """Block external Python socket connections/DNS in the API child."""
    if event == "socket.connect":
        address = args[1]
        host = address[0] if isinstance(address, tuple) else ""
    elif event in ("socket.getaddrinfo", "socket.gethostbyname", "socket.gethostbyaddr"):
        host = args[0]
        if host is None:
            return
    else:
        return
    if host == "localhost":
        return
    try:
        allowed = ipaddress.ip_address(host).is_loopback
    except ValueError:
        allowed = False
    if not allowed:
        raise PermissionError("Lab 4 API denies external network access")


def serve():
    import runpy
    sys.addaudithook(loopback_only)
    sys.path.insert(0, str(ROOT))
    sys.argv = ["app", "--port", "5000"]
    runpy.run_module("app", run_name="__main__")


def run():
    os.chdir(ROOT)
    REPORTS.mkdir(exist_ok=True)
    scenarios = [("preflight", 5, 5, "6s"), ("A", 10, 2, "30s"),
                 ("B", 50, 5, "60s"), ("C", 200, 50, "30s")]
    for label, *_ in scenarios:
        if list(REPORTS.glob(label + ".*")) or list(REPORTS.glob(label + "_*")):
            raise FileExistsError(f"Preserve existing reports/{label} outputs before rerunning")
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        with opener.open("http://127.0.0.1:5000/health", timeout=1):
            raise RuntimeError("Port 5000 already serves an API; stop it before this managed run")
    except (OSError, urllib.error.URLError):
        pass
    results = {}
    api_log = REPORTS / "lab4-api.log"
    with api_log.open("x", encoding="utf-8") as log:
        server = subprocess.Popen([sys.executable, "-B", str(Path(__file__).resolve()), "--serve"],
                                  cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
        try:
            for attempt in range(100):
                if server.poll() is not None:
                    raise RuntimeError("API startup failed; inspect reports/lab4-api.log")
                try:
                    with opener.open("http://127.0.0.1:5000/health", timeout=1) as response:
                        if json.load(response) == {"status": "ok"}:
                            break
                except (OSError, urllib.error.URLError):
                    time.sleep(0.1)
            else:
                raise RuntimeError("API readiness timed out")
            print("Existing Books API ready on loopback port 5000; external egress denied", flush=True)
            for label, users, rate, duration in scenarios:
                command = [sys.executable, "-B", "-m", "locust", "-f", "performance/locustfile.py",
                           "--headless", "-u", str(users), "-r", str(rate), "-t", duration,
                           "--host", "http://127.0.0.1:5000", "--stop-timeout", "10", "--only-summary",
                           "--html", f"reports/{label}.html", "--csv", f"reports/{label}"]
                print(f"Running {label}: users={users}, spawn_rate={rate}, duration={duration}", flush=True)
                started = time.perf_counter()
                with (REPORTS / f"{label}.log").open("x", encoding="utf-8") as output:
                    completed = subprocess.run(command, cwd=ROOT, stdout=output, stderr=subprocess.STDOUT)
                elapsed = time.perf_counter() - started
                diagnostic = json.loads((REPORTS / f"{label}_diagnostics.json").read_text(encoding="utf-8"))
                total = diagnostic["aggregate"]
                results[label] = {"users": users, "spawn_rate": rate, "duration": duration,
                                  "exit_code": completed.returncode, "wall_seconds": round(elapsed, 3),
                                  "command": command[3:], "aggregate": total}
                (REPORTS / "run_summary.json").write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
                print(f"Finished {label}: exit={completed.returncode}, wall={elapsed:.3f}s, "
                      f"requests={total['requests']}, failures={total['failures']}", flush=True)
                if label == "preflight" and completed.returncode:
                    raise RuntimeError("Smoke test failed; official scenarios were not started")
            with opener.open("http://127.0.0.1:5000/books?author=locust-lab4", timeout=5) as response:
                leftovers = json.load(response)
                if leftovers:
                    raise RuntimeError("Load-test books remain; inspect diagnostics before cleanup")
            print("Completed A/B/C sequentially; no load-test books remain", flush=True)
        finally:
            if server.poll() is None:
                server.terminate()
            server.wait(timeout=10)


if __name__ == "__main__":
    if sys.argv[1:] == ["--serve"]:
        serve()
    else:
        run()
