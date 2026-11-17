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

Install Newman once, if it is not already available:

```powershell
npm.cmd install -g newman
```

Run all seven requests and write a real JUnit report to `junit.xml`:

```powershell
newman.cmd run books-api.postman_collection.json `
  -e postman/local.postman_environment.json `
  -r cli,junit `
  --reporter-junit-export junit.xml
$LASTEXITCODE
```

If a global install is unavailable, install and run Newman locally instead:

```powershell
npm.cmd install --no-save --package-lock=false newman
.\node_modules\.bin\newman.cmd run books-api.postman_collection.json -e postman/local.postman_environment.json -r cli,junit --reporter-junit-export junit.xml
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

### Verification status (2026-11-17)

Static validation passed for both matching collection JSON files: seven requests
in the required order, 17 `pm.test()` blocks (at least two per request), valid
JavaScript syntax and JSON bodies, and the existing local environment resolving
`base_url`. The existing pytest suite passed all six tests in 0.77 seconds using
the project's parent Python environment.

Newman was unavailable, and installing it from npm failed with `EACCES` because
network access was blocked in the execution environment. No Newman run, assertion
pass/fail counts, JUnit testcase count, or collection duration has been measured;
no `junit.xml` was generated. The 7 requests / 17 assertions / 17 JUnit testcases
above describe the expected successful run, not a recorded Newman result.

## 5. Lab 4 — Locust

`performance/locustfile.py` là baseline có weighted tasks; `performance/locustfile_realistic.py` minh hoạ flow có state và demo login. Chạy API trong terminal 1; terminal 2:

```bash
mkdir -p reports
locust -f performance/locustfile.py --headless -H http://127.0.0.1:5000 \
  -u 10 -r 2 -t 30s --html reports/A.html
locust -f performance/locustfile.py --headless -H http://127.0.0.1:5000 \
  -u 50 -r 5 -t 60s --html reports/B.html
locust -f performance/locustfile.py --headless -H http://127.0.0.1:5000 \
  -u 200 -r 50 -t 30s --html reports/C.html
```

Hoàn thiện TODO `search_by_year` và nếu tạo 1% failure giả lập, **ghi rõ** đó là HTTP 500 do server phát hay client-side `response.failure()` của Locust. Điền `performance/analysis.md` bằng kết quả **đo thực tế**; báo cáo p95, failure rate, RPS, nhận xét giới hạn phép đo. Load test chạy Flask development server + SQLite chỉ có ý nghĩa thực hành, không thể khẳng định SLO production.

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
