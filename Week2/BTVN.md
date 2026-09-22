
GitHub REST API

### Endpoint 1: Get a repository

**Endpoint:**

`GET /repos/{owner}/{repo}`

**Ví dụ:**

`GET /repos/octocat/Hello-World`

**Method:** `GET`

**Status code:**
- `200 OK`: Lấy repository thành công.
- `404 Not Found`: Repository không tồn tại hoặc không thể truy cập.

**Headers:**
```http
Accept: application/vnd.github+json
X-GitHub-Api-Version: 2022-11-28
RESTful: Có.

Lý do: URI xác định resource repository và sử dụng HTTP method GET để lấy resource.


Endpoint 2: List repository issues

Endpoint:

GET /repos/{owner}/{repo}/issues

Ví dụ:

GET /repos/octocat/Hello-World/issues

Method: GET

Status code:

200 OK: Lấy danh sách issues thành công.
404 Not Found: Repository không tồn tại.
422 Unprocessable Content: Request không hợp lệ.

Headers:
Accept: application/vnd.github+json
X-GitHub-Api-Version: 2022-11-28



RESTful: Có.

Lý do: /issues đại diện cho một collection resource và GET được sử dụng để lấy collection đó.

Endpoint 3: Get an issue

Endpoint:

GET /repos/{owner}/{repo}/issues/{issue_number}

Ví dụ:

GET /repos/octocat/Hello-World/issues/1

Method: GET

Status code:

200 OK: Lấy issue thành công.
404 Not Found: Issue hoặc repository không tồn tại.

Headers:
Accept: application/vnd.github+json
X-GitHub-Api-Version: 2022-11-28


RESTful: Có.

Lý do: URI xác định một issue cụ thể bằng issue_number và sử dụng GET để lấy resource.

Endpoint 4: List pull requests

Endpoint:

GET /repos/{owner}/{repo}/pulls

Ví dụ:

GET /repos/octocat/Hello-World/pulls

Method: GET

Status code:

200 OK: Lấy danh sách pull requests thành công.
404 Not Found: Repository không tồn tại.

Headers:


Accept: application/vnd.github+json
X-GitHub-Api-Version: 2022-11-28


RESTful: Có.

Lý do: /pulls đại diện cho collection pull requests và GET được sử dụng để lấy collection.

Endpoint 5: Get repository contents

Endpoint:

GET /repos/{owner}/{repo}/contents/{path}

Ví dụ:

GET /repos/octocat/Hello-World/contents/README.md

Method: GET

Status code:

200 OK: Lấy nội dung thành công.
404 Not Found: File hoặc repository không tồn tại.

Headers:
Accept: application/vnd.github+json
X-GitHub-Api-Version: 2022-11-28
RESTful: Có.

Lý do: URI xác định resource content thông qua path và sử dụng GET để lấy representation của resource.
