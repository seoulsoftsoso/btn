### 실행방법 
```bash
# Configure your virtualenv or venv or something like that stuff..
$ python -m venv  web #you can set different name instead of 'web'
$ source web/Scripts/activate # you can set different name instead of 'web'

$ pip install django
$ pip install mysqlclient
$ pip freeze > requirements.txt 
$ pip install -r requirements.txt

$ git clone https://github.com/seoulsoftsoso/button.git
$ cd button

$ python manage.py makemigrations 
$ python manage.py migrate
$ python manage.py collectstatic
$ python manage.py runserver
```


### manage.py 명령 실행시
manage.py 안의 main > KPICALL() 함수를 주석 처리 후 실행해 주세요.
KPICALL() 함수는, 스마트공장 솔루션에 로그 자동 전송 API 입니다.
KPICALL() 함수를 사용할때는 runserver에 --noreload 옵션을 주세요.
  KPICALL() 함수가 두번 돌아가는 것을 방지하는 옵션입니다. 
