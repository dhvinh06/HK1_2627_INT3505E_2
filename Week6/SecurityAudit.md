
API social-network: `POST /auth/login`, `POST /auth/refresh`, `GET /posts/{id}`.

 1. BOLA trên `GET /posts/{id}` (OWASP API1:2023)
- Rủi ro: User A có token và scope `posts:read` hợp lệ nhưng đọc được bài private/friends của B bằng cách đổi `id`. Id tuần tự (1, 2, 3...) dễ bị dò.
- Giảm thiểu: Kiểm tra quyền trên từng object (chủ bài, bạn bè, chia sẻ). Trả 404 thay vì 403 cho bài không có quyền để không lộ sự tồn tại. Cân nhắc dùng UUID thay id tuần tự (chỉ là lớp phụ, không thay thế kiểm quyền).

 2. Brute force / credential stuffing ở `POST /auth/login` (OWASP API2:2023)
- Rủi ro: Không giới hạn số lần thử thì kẻ tấn công thử hàng loạt mật khẩu hoặc danh sách credential bị lộ từ nơi khác.
- Giảm thiểu: Rate-limit theo IP và theo tài khoản, tăng dần độ trễ, CAPTCHA/MFA khi bất thường. Tránh khóa cứng tài khoản vì gây từ chối dịch vụ.

 3. Lộ thông tin tài khoản qua lỗi và thời gian phản hồi
- Rủi ro: Thông báo "email không tồn tại" khác "sai mật khẩu", hoặc thời gian phản hồi khác nhau (không chạy bcrypt khi email không tồn tại), cho phép dò email đã đăng ký.
- Giảm thiểu: Luôn trả cùng một lỗi `invalid_credentials` (401). Chạy hash giả khi không tìm thấy user để cân bằng thời gian.

 4. Lưu token ở `localStorage` (phía client web)
- Rủi ro: Mọi JavaScript trong trang (kể cả bị XSS) đọc được access/refresh token và mang đi dùng.
- Giảm thiểu: Với web, dùng BFF và cookie HttpOnly + Secure + SameSite, kèm chống CSRF. Chống XSS bằng CSP và escape output. Access token sống ngắn (15 phút).

 5. Refresh token bị đánh cắp / không thu hồi được
- Rủi ro: Refresh token sống 30 ngày. Nếu lộ, kẻ tấn công liên tục lấy access token mới. JWT stateless nên logout không vô hiệu được nếu thiếu blocklist.
- Giảm thiểu: Lưu `jti` refresh token ở server (DB/Redis) để thu hồi. Rotate refresh token mỗi lần dùng và phát hiện tái sử dụng token cũ thì hủy cả chuỗi phiên. Logout phải thu hồi cả access và refresh.

 6. Cấu hình JWT sai (alg, secret, aud/iss)
- Rủi ro: Chấp nhận `alg=none`, algorithm confusion HS/RS, secret yếu hoặc hardcode trong code/commit lên Git, không kiểm `aud`/`iss` nên token dịch vụ này dùng được ở dịch vụ khác.
- Giảm thiểu: Allowlist thuật toán cố định, secret ngẫu nhiên >= 256 bit nạp từ biến môi trường/secret manager, hỗ trợ `kid` để rotate khóa, luôn kiểm `exp`, `iss`, `aud`.

 7. Nhầm lẫn access token và refresh token ở `/auth/refresh`
- Rủi ro: Nếu endpoint chấp nhận cả access token, hoặc `/posts` chấp nhận refresh token, thì token sống dài bị dùng sai mục đích và vòng đời token mất ý nghĩa.
- Giảm thiểu: Thêm claim `type` (access/refresh) và kiểm tra chặt tại từng endpoint. Dùng đúng `@jwt_required(refresh=True)` cho `/auth/refresh`.

 8. Lộ dữ liệu thừa trong payload JWT và response (OWASP API3:2023)
- Rủi ro: Payload JWT ai cũng đọc được nên không được chứa PII hay secret. Response bài viết có thể lộ field nội bộ (email tác giả, `password_hash`, cờ nội bộ) nếu trả thẳng row từ DB.
- Giảm thiểu: Claims chỉ gồm `sub`, `scopes`, `exp`, `jti`... Response qua DTO whitelist field.

 9. Thiếu HTTPS và log chứa credential
- Rủi ro: Gửi password/token qua HTTP thường bị nghe lén. Log request ghi cả body login hoặc header `Authorization` làm lộ credential cho người truy cập log.
- Giảm thiểu: Bắt buộc TLS, bật HSTS. Che (mask) password, token và header `Authorization` trong log.

 10. Thiếu kiểm tra mặc định deny và quyền ở mức hàm (OWASP API5:2023)
- Rủi ro: Thêm endpoint mới mà quên gắn decorator xác thực/phân quyền thì endpoint đó vô tình public.
- Giảm thiểu: Middleware tập trung, mặc định từ chối, chỉ whitelist rõ các endpoint public (`/auth/login`). Có kiểm thử cho 401/403 ở mọi route.
