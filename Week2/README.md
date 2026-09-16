Bài 1:
test list rỗng :
(.venv) PS D:\Project 2026 java\SOA> curl.exe http://127.0.0.1:5000/books
{
"data": [],
"total": 0
}

test post
(.venv) PS D:\Project 2026 java\SOA> curl.exe --% -X POST http://127.0.0.1:5000/books -H "Content-Type: application/json" -d "{\"title\":\"Clean Code\",\"author\":\"R.Martin\"}"
{
"author": "R.Martin",
"id": 1,
"title": "Clean Code"
}


Bài 2 :
(.venv) PS D:\Project 2026 java\SOA> curl.exe --% -X PATCH http://127.0.0.1:5000/books/1 -H "Content-Type: application/json" -d "{\"price\":19.99}"    
{
"author": "X",
"id": 1,
"isbn": null,
"price": 19.99,
"title": "New"
}price từ null đổi thành 19.99

Test PUT
(.venv) PS D:\Project 2026 java\SOA> curl.exe --% -X PUT http://127.0.0.1:5000/books/1 -H "Content-Type: application/json" -d "{\"title\":\"New\",\"author\":\"X\"}"
{
"author": "X",
"id": 1,
"isbn": null,
"price": null,
"title": "New"
}PUT thay thế mọi trường không điền thành null


Test DELETE :
(.venv) PS D:\Project 2026 java\SOA> curl.exe -X DELETE -i http://127.0.0.1:5000/books/1                                                           
HTTP/1.1 204 NO CONTENT
Server: Werkzeug/3.1.8 Python/3.14.0
Date: Wed, 16 Sep 2026 08:41:08 GMT
Content-Type: text/html; charset=utf-8
Connection: close     
đã xóa thành công, gửi 204

Bài 3:



