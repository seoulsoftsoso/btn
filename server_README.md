- 현재 nginx,gunicorn,daphne daemon으로 running중.  
  
- 프로젝트경로 - /home/dev3/Button_Project/btn  
- 가상환경 - cd /home/dev3/Button_Project  source web/bin/activate  

- 업데이트(경로: 프로젝트경로)  
가상환경 내에서  
pip install -r requirements.txt  
git pull  
sudo systemctl restart gunicorn  
sudo systemctl restart nginx  
sudo systemctl restart daphne(만약 인증서쪽 변화있다면)  

