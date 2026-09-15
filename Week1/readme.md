bài 1 :
execute : python app1.py

test :
(.venv) PS D:\Project 2026 java\SOA> curl.exe -i http://127.0.0.1:5000/
HTTP/1.1 200 OK
Server: Werkzeug/3.1.8 Python/3.14.0
Date: Wed, 09 Sep 2026 08:43:25 GMT
Content-Type: application/json
Content-Length: 31
Connection: close

{
"message": "Hello, API!"
}

bài 2:
(.venv) PS D:\Project 2026 java\SOA\Week1> curl.exe -i http://127.0.0.1:5000/health
HTTP/1.1 200 OK
Server: Werkzeug/3.1.8 Python/3.14.0
Date: Sun, 13 Sep 2026 17:23:27 GMT
Content-Type: application/json
Content-Length: 21
Connection: close

{
"status": "ok"
}
hoặc là vào thẳng  http://127.0.0.1:5000/health vì chỉ là GET

(.venv) PS D:\Project 2026 java\SOA\Week1> curl.exe -i http://127.0.0.1:5000/echo -H "Content-Type: application/json" -d '{\"name\":\"An\",\"age\":21}'
HTTP/1.1 200 OK
Server: Werkzeug/3.1.8 Python/3.14.0
Date: Sun, 13 Sep 2026 17:30:36 GMT
Content-Type: application/json
Content-Length: 56
Connection: close

{
"you_sent": {
"age": 21,
"name": "An"
}
}

bài 3 :
curl.exe -i -X POST http://127.0.0.1:5000/students -H "Content-Type: application/json" -d '{\"name\":\"An\",\"gpa\":3.4}'
HTTP/1.1 201 CREATED
Server: Werkzeug/3.1.8 Python/3.14.0
Date: Mon, 14 Sep 2026 10:55:26 GMT
Content-Type: application/json
Content-Length: 81
Connection: close

{
"gpa": 3.4,
"id": "f1e42365-403f-43c1-ba5d-f3b2a8ecc36a",
"name": "An"
}

bài 4 :
ko chạy được do findById chưa define

bài 5:
curl.exe -i -X DELETE http://127.0.0.1:5000/orders/abc-xyz

HTTP/1.1 404 NOT FOUND
Server: Werkzeug/3.1.8 Python/3.14.0
Date: Mon, 14 Sep 2026 11:24:51 GMT
Content-Type: application/json
Content-Length: 27
Connection: close

{
"error": "not found"
}

bài 6:
(.venv) PS D:\Project 2026 java\SOA> curl.exe -i http://127.0.0.1:5000/books         

HTTP/1.1 200 OK                                                                      
Server: Werkzeug/3.1.8 Python/3.14.0
Date: Tue, 15 Sep 2026 07:14:59 GMT
Content-Type: application/json
Content-Length: 78
Connection: close

[
{
"author": "R. Martin",
"id": 1,
"title": "Clean Code"
}
]

(.venv) PS D:\Project 2026 java\SOA> curl.exe -i -X POST http://127.0.0.1:5000/books -H "Content-Type: application/json" -d '{\"title\":\"DDIA\",\"author\":\"Kleppmann\"}'                                                                                    
HTTP/1.1 201 CREATED
Server: Werkzeug/3.1.8 Python/3.14.0
Date: Tue, 15 Sep 2026 07:21:42 GMT
Content-Type: application/json
Content-Length: 58
Location: /books/2
Connection: close

{
"author": "Kleppmann",
"id": 2,
"title": "DDIA"
}

_next sửa thành 2 vì có sẵn id 1 trong code mẫu, nếu _next =1 thì sẽ có 2 book có id là 1




