# Lab 4 — Phân tích kiểm thử tải Books API

Ngày kiểm tra: **18/11/2026**, giờ Việt Nam. Môi trường: Windows, Python 3.14,
Locust 2.47.0, Flask development server tại `127.0.0.1:5000`, SQLite cục bộ.
Client và server dùng cùng máy. Backend, OpenAPI, Postman và JUnit Lab 3 giữ nguyên.

## 1. Trạng thái thực thi và bằng chứng

- Import thành công; Locust đăng ký `BooksUser` với trọng số list/read/search/create
  là **3/2/2/1**, `between(1, 3)`; có `search_by_year(self, year=2017)`.
- Kiểm tra logic độc lập: 1.000 quyết định giả lập tạo đúng 10 quyết định lỗi
  (đây là kiểm tra trong bộ nhớ, không phải 1.000 HTTP request). Đã kiểm tra lỗi
  HTTP 500 thật không bị giả lập che mất, HTTP 200 không bị đổi status, không xóa
  id không thuộc user và từ chối target ngoài localhost.
- `reports/smoke.*`: thử nghiệm đầu thất bại vì API không còn lắng nghe; 10 request,
  10 lỗi kết nối. Không dùng lần này để đánh giá hiệu năng API.
- `reports/preflight.html`: smoke test thật với 5 user, spawn 5/s, cấu hình 6 giây,
  exit code **0**, hoàn thành và dọn hết sách đã tạo. Tiến trình mất **6,862 giây**
  gồm khởi động CLI; thời gian hoạt động trong HTML làm tròn thành 5 giây.
- **A** đã bắt đầu đúng 10 user, spawn 2/s, cấu hình 30 giây, nhưng bị ngắt trước
  khi hoàn thành. Chỉ có log/CSV tiến độ; không có `A.html` hay thống kê cuối.
- **B và C chưa bắt đầu**. Không có báo cáo HTML chính thức A/B/C.

**Nguyên nhân chặn:** automatic approval review từ chối tiến trình do phát hiện
kết nối tới một telemetry host bên ngoài với payload chưa xác định. Lần thử lại
với launcher chặn external Python socket/DNS trong API child vẫn bị từ chối.
Không tiếp tục khởi động server sau lần từ chối thứ hai và không suy đoán payload.
Các lần chạy chưa hoàn tất không được coi là benchmark thành công.

Sau khi xác nhận cổng 5000 không còn lắng nghe, đã dọn 10 fixture từ lần A bị ngắt,
chỉ khớp author `locust-lab4`, title `Locust ` + UUID 32 ký tự hex, year 2017,
ISBN null. Còn **0 sách Lab 4**; bằng chứng tại `reports/interrupted_A_cleanup.json`.
Không xóa dữ liệu khác.

## 2. Bảng so sánh ba kịch bản yêu cầu

| Metric | Scenario A | Scenario B | Scenario C |
|---|---|---|---|
| Concurrent users (cấu hình) | 10 | 50 | 200 |
| Spawn rate (users/s) | 2 | 5 | 50 |
| Duration (cấu hình) | 30 s | 60 s | 30 s |
| Trạng thái | Bị ngắt, chưa hoàn tất | Chưa chạy | Chưa chạy |
| Total requests (kết quả đầy đủ) | Chưa có | Chưa có | Chưa có |
| Failed requests | Chưa có | Chưa có | Chưa có |
| Failure rate | Chưa có | Chưa có | Chưa có |
| Average latency | Chưa có | Chưa có | Chưa có |
| p50 | Chưa có | Chưa có | Chưa có |
| p95 | Chưa có | Chưa có | Chưa có |
| p99 | Chưa có | Chưa có | Chưa có |
| RPS | Chưa có | Chưa có | Chưa có |
| SLO p95 < 300 ms | Chưa đánh giá | Chưa đánh giá | Chưa đánh giá |

Không thay thế số liệu A/B/C bằng số liệu preflight hoặc nội suy theo số user.
`A_stats.csv` là snapshot của lần bị ngắt; nó không chứng minh hoàn thành 30 giây.

### Số đo preflight thực tế (không phải Scenario A)

| Metric | Giá trị |
|---|---:|
| Users / spawn rate | 5 / 5 users/s |
| Total requests | 30 |
| Failed requests / failure rate | 0 / 0% |
| Average latency | 26,329 ms |
| p50 | 11 ms |
| p95 | 110 ms |
| p99 | 120 ms |
| RPS | 5,334 |
| Genuine HTTP 500 / transport / contract failures | 0 / 0 / 0 |
| Synthetic failures / expected 404 | 0 / 0 |

Nguồn: thống kê cuối nhúng trong HTML thật của Locust, CLI log và diagnostics.
CSV được ghi định kỳ nên snapshot preflight cuối chỉ có 23 request trước khi
cleanup hoàn tất; HTML/CLI cuối có 30. `run_summary.json` và diagnostics đã được
bổ sung số liệu cuối đọc từ chính HTML, giữ snapshot CSV ban đầu để đối chiếu.
Code hiện tại xuất thống kê trực tiếp từ Locust tại shutdown để tránh nhầm này;
phần xuất thống kê mới chưa được chạy lại với HTTP vì bị chặn thực thi.

| Endpoint/request name | Requests | Failed | HTTP thực tế | p95 (ms) |
|---|---:|---:|---|---:|
| GET /books | 6 | 0 | 200 | 6 |
| GET /books/{id} | 7 | 0 | 200 | 60 |
| GET /books?year={year} | 3 | 0 | 200 | 7 |
| POST /books | 2 | 0 | 201 | 12 |
| POST /books (setup) | 5 | 0 | 201 | 120 |
| DELETE /books/{id} | 2 | 0 | 204 | 12 |
| DELETE /books/{id} (cleanup) | 5 | 0 | 204 | 76 |

Setup/cleanup là HTTP request được đo và nằm trong tổng. p95/p99 được Locust
làm tròn; với 30 mẫu, percentile nhạy với vài request chậm và chưa ổn định.

## 3. Cơ chế giả lập khoảng 1%

API đã hỗ trợ `GET /books?year=2017`; không thêm route hoặc sửa Flask.
Chỉ sau khi response HTTP 200 có JSON/list/Book hợp lệ và tất cả year khớp,
request tìm kiếm hợp lệ thứ 100, 200, 300... trong mỗi tiến trình được đánh dấu
`response.failure(SYNTHETIC_ERROR)`. Nội dung lỗi rõ ràng là
`SYNTHETIC_HTTP_500: Locust simulation; server returned HTTP 200`.

HTTP status thật vẫn là **200**, không phải Flask phát HTTP 500. Lỗi HTTP thật,
timeout và sai contract được phân loại trước nên không bị che. Tỷ lệ bằng
floor(N/100)/N với N là số tìm kiếm hợp lệ; N nhỏ hơn 100 có 0 lần giả lập.
Preflight có 3 search hợp lệ nên 0 lỗi giả lập là đúng thiết kế. Tỷ lệ trên toàn
bộ request thấp hơn 1% vì các task và setup/cleanup khác không được tiêm lỗi.

Counter reset mỗi run standalone; random seed cố định hỗ trợ lặp lại workload,
nhưng lịch chạy đồng thời, UUID, latency và tổng số request vẫn có thể khác.
Run có lỗi giả lập thường exit 1: phải đọc failure CSV/diagnostics, không đổi
exit code để làm kết quả trông thành công. `remaining_owned_ids` hỗ trợ phát hiện
cleanup chưa hoàn thành khi tiến trình kết thúc bình thường.

## 4. Trả lời câu hỏi

### Câu 1 — Kịch bản nào có p95 cao nhất, vì sao?

**Chưa xác định được**, vì không có benchmark đầy đủ A/B/C. Preflight có p95
110 ms, trong đó setup POST có p95 120 ms, nhưng chỉ ở 5 user. Không thể suy ra
C cao nhất từ số user. Khi có kết quả, so sánh p95 aggregate và từng endpoint,
request count/RPS và thời gian ramp-up. SQLite ghi tuần tự, tranh chấp connection
và scheduling giữa client/server cùng máy là các giả thuyết cần số đo kiểm chứng.

### Câu 2 — Endpoint nào tăng failure rate khi tăng số user?

**Chưa đủ dữ liệu để kết luận xu hướng.** Toàn bộ endpoint trong preflight có
0 lỗi thật; không có cặp benchmark A/B/C đầy đủ để so sánh. Không gán lỗi kết nối
của lần smoke đầu hay việc A bị hệ thống dừng cho khả năng chịu tải của Flask.

Khi chạy đủ, tách `synthetic_failures` khỏi `server_failures`, `transport_failures`
và `contract_failures` trong diagnostics. HTTP 404 đúng `NOT_FOUND` là kết quả
nghiệp vụ hợp lệ. POST/DELETE có thể gặp tranh chấp ghi SQLite khi tăng tải,
nhưng đây là khả năng từ code, không phải lỗi đã quan sát trong preflight.

### Câu 3 — SLO p95 < 300 ms

**A/B/C: chưa đánh giá; chưa thể gán PASS hay FAIL.** Preflight riêng lẻ có
110 < 300 ms, nên đạt ngưỡng cho lần smoke 5 user đó; không đại diện ba kịch bản.

Đề xuất performance gate tương lai: Scenario A (10 user, spawn 2/s, 30 s,
wait 1–3 s) trên runner cố định và DB fixture giống nhau, có warm-up riêng trước
đo. Yêu cầu p95 < 300 ms, ít nhất 100 request và **0 lỗi thật**, đồng thời kiểm tra
số synthetic đúng counter và cleanup hoàn tất. Đọc diagnostics thay vì bỏ qua
exit 1. Dùng B/C ở bước kiểm tra định kỳ để giảm nhiễu và thời gian CI. Chỉ chốt
baseline sau khi đo lặp lại; chưa có bằng chứng A đạt ngưỡng trên máy hiện tại.

### Bonus — Chỉ 5 connection khi có 200 user

**Chưa thực hiện thí nghiệm giới hạn pool.** Kiểm tra engine SQLite hiện tại cho
thấy `QueuePool`, pool_size=5, max_overflow=10, pool_timeout=30 s. Vì vậy chỉ đặt
pool_size=5 không đồng nghĩa tối đa 5 connection: cần max_overflow=0.

Với tối đa 5 connection, request giữ được connection sẽ xử lý; request khác
chờ pool. Nếu thời gian giữ connection dài, queueing có thể tăng p95/p99.
Chờ quá pool_timeout có thể gây SQLAlchemy TimeoutError/HTTP 500; client Locust
(timeout 5 s trong file hiện tại) cũng có thể timeout trước. SQLite còn có tranh
chấp ghi riêng, nên tăng pool không tự loại bỏ giới hạn ghi.

Để kiểm chứng: dùng cấu hình test tách biệt qua `create_app(config=...)`, đặt
SQLALCHEMY_ENGINE_OPTIONS gồm pool_size=5, max_overflow=0 và pool_timeout được
ghi rõ; chạy lại C trên cùng dữ liệu/workload, so sánh p95/p99, RPS, lỗi thật,
server log và thời gian chờ pool với baseline. Không thay đổi API production.

## 5. Hoàn tất kiểm chứng

Lệnh PowerShell để bật API và chạy chính xác A/B/C nằm trong phần Lab 4 của
`README.md`. Giữ/di chuyển các output A bị ngắt trước khi chạy lại. Launcher
`performance/run_load_tests.py` chạy preflight/A/B/C lần lượt và từ chối ghi đè
report có sẵn. Không có báo cáo A/B/C giả được tạo.

Kiểm tra hồi quy hiện có: **6 passed, 0 failed trong 0,35 giây**. Hash của
Postman collections, `junit.xml` và CLI log Lab 3 được kiểm tra giữ nguyên.
