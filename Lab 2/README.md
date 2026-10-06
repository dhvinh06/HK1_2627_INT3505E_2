test 404 : curl.exe -i curl.exe -i http://127.0.0.1:5000/resources/999

![img.png](img.png)

ko co Accept : curl.exe -i -H "Accept:" http://127.0.0.1:5000/resources/999
![img_1.png](img_1.png)

co Accept : curl.exe -i -H "Accept: application/json" http://127.0.0.1:5000/resources/999
![img_2.png](img_2.png)

route k ton tai : curl.exe -i http://127.0.0.1:5000/abc
![img_3.png](img_3.png)

500 : curl.exe -i http://127.0.0.1:5000/boom
![img_4.png](img_4.png)