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
test HATEOAS
.venv) PS D:\Project 2026 java\SOA> curl.exe -i "http://127.0.0.1:5000/books?page=2&size=10"
HTTP/1.1 200 OK
Server: Werkzeug/3.1.8 Python/3.14.0
Date: Tue, 22 Sep 2026 09:52:10 GMT
Content-Type: application/json
Content-Length: 363
Cache-Control: public, max-age=30
Connection: close

{
"_links": {
"first": {
"href": "/books?page=1&size=10"
},
"last": {
"href": "/books?page=1&size=10"
},
"prev": {
"href": "/books?page=1&size=10"
},
"self": {
"href": "/books?page=2&size=10"
}
},
"data": [],
"pagination": {
"page": 2,
"size": 10,
"total": 0,
"total_pages": 0
}
}


(.venv) PS D:\Project 2026 java\SOA> curl.exe --% -X POST http://127.0.0.1:5000/books -H "Content-Type: application/json" -d "{\"title\":\"1984\",\"author\":\"Orwell\"}"        
{
"author": "Orwell",
"id": 1,
"title": "1984"
}    mồi data

Test author :
(.venv) PS D:\Project 2026 java\SOA> curl.exe -i "http://127.0.0.1:5000/books?author=Orwell"                                                                              
HTTP/1.1 200 OK
Server: Werkzeug/3.1.8 Python/3.14.0
Date: Tue, 22 Sep 2026 10:11:18 GMT
Content-Type: application/json
Content-Length: 382
Cache-Control: public, max-age=30
Connection: close

{
"_links": {
"first": {
"href": "/books?page=1&size=20"
},
"last": {
"href": "/books?page=1&size=20"
},
"self": {
"href": "/books?page=1&size=20"
}
},
"data": [
{
"author": "Orwell",
"id": 1,
"title": "1984"
}
],
"pagination": {
"page": 1,
"size": 20,
"total": 1,
"total_pages": 1
}
}

Test clean:
(.venv) PS D:\Project 2026 java\SOA> curl.exe -i "http://127.0.0.1:5000/books?q=clean"      
HTTP/1.1 200 OK
Server: Werkzeug/3.1.8 Python/3.14.0
Date: Tue, 22 Sep 2026 10:12:47 GMT
Content-Type: application/json
Content-Length: 304
Cache-Control: public, max-age=30
Connection: close

{
"_links": {
"first": {
"href": "/books?page=1&size=20"
},
"last": {
"href": "/books?page=1&size=20"
},
"self": {
"href": "/books?page=1&size=20"
}
},
"data": [],
"pagination": {
"page": 1,
"size": 20,
"total": 0,
"total_pages": 0
}
}

Test -H "Accept: application/json" : k có ý nghĩa lắm vì toàn trả jsonify()





