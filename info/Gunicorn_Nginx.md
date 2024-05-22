### 실행방법 
```bash
#README_web.md 이후의 프로세스
# 참고 YOUTUBE : https://youtu.be/NSHshIEVL-M?si=Hv-S2VO_RYMId0gi

#경로는 git clone ~ 후 cd button (이 경로 아래에 button또있는데 구분필요)
$ pip install gunicorn
$ gunicorn --bind 0.0.0.0:8000 button.wsgi
$ sudo vi /etc/systemd/system/gunicorn.socket
#파일 내부 
#[Unit]
#Description=test django
#
#[Socket]
#ListenStream=/run/gunicorn.sock
#
#[Install]
#WantedBy=socekts.target

$ sudo vi /etc/systemd/system/gunicorn.service
#파일 내부
# [Unit]
# Description=gunicorn daemon
# Requires=gunicorn.socket
# After=network.target

# [Service]
# User=dev3
# Group=www-data
# WorkingDirectory=/home/dev3/Button_Project/button
# ExecStart=/home/dev3/Button_Project/web/bin/gunicorn \
#           --access-logfile - \
#           --workers 3 \
#           --bind unix:/run/gunicorn.sock \
#           button.wsgi:application

# [Install]
# WantedBy=multi-user.target

$ sudo systemctl start gunicorn.socket
$ sudo systemctl enable gunicorn.socket
$ file /run/gunicorn.sock
$ curl --unix-socket /run/gunicorn.sock localhost

$ sudo vi /etc/nginx/sites-available/button
#파일내부
# server {
#         listen 80;
#         server_name 118.44.218.236; #public IP

#         location = /favicon.ico { access_log off; log_not_found off; }
#         location /static/ {
#                 root /home/dev3/Button_Project/button;

#         }

#         location / {
#                 proxy_pass http://unix:/run/gunicorn.sock;
#                 proxy_set_header Host $host;
#                 proxy_set_header X-Real-IP $remote_addr;
#                 proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
#                 proxy_set_header X-Forwarded-Proto $scheme;
#         }
#         #location \ {
#         #       include proxy_params;
#         #       proxy_pass http://unix:/run/gunicorn.sock;
#         #       
#         #}

# }

$ sudo ln -s /etc/nginx/sites-available/button /etc/nginx/sites-enabled
$ sudo nginx -t
$ sudo systemctl restart nginx

#optional, 디자인 적용 안될때
$ sudo vi /etc/nginx/nginx.conf  #이 안에 들어가서 첫번째줄 user이 www-data로 되어있을텐데 본인 user로 수정해주기.


####
#수정관리는 
$ git pull
$ sudo systemctl restart gunicorn
$ sudo systemctl restart nginx


#포트포워딩 필요. 현재는 7000번 포트 사용중.
