test theo yeu cau : curl.exe -i 'localhost:5000/orders?status=paid'
![img.png](img.png)
curl.exe -i  'localhost:5000/orders?limit=5'  
![img_1.png](img_1.png)
curl.exe -i 'localhost:5000/orders?fields=id,total'
![img_2.png](img_2.png)

curl.exe -i 'localhost:5000/orders?limit=5&cursor=<next_cursor>'
![img_3.png](img_3.png)

curl.exe -i 'localhost:5000/orders?cursor=abc'
![img_4.png](img_4.png)

cursor + sort : curl.exe -s 'localhost:5000/orders?sort=total&limit=5&fields=id,total'
![img_5.png](img_5.png) total bang nhau thi id tang dan

curl.exe -s 'localhost:5000/orders?sort=-total&limit=5&fields=id,total'   sort giam 
![img_6.png](img_6.png)  total = nhau thi id giam 