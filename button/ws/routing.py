from django.urls import re_path, path

import logging
from button.ws import consumers

logger = logging.getLogger(__name__)

websocket_urlpatterns = [
    re_path(r'ws/landing/user/$', consumers.MyConsumer.as_asgi()),
    # path('ws/flutter/gtrsen', consumers.AppConsumer.as_asgi()),  # New WebSocket route
    re_path(r'^ws/flutter/gtrsen/(?P<conId>\d+)/$', consumers.AppConsumer.as_asgi()),  # URL에서 conId를 추출
    re_path(r'^ws/flutter/term/(?P<conId>\d+)/$', consumers.FlutterTermConsumer.as_asgi()),  # URL에서 conId를 추출

]
logger.info('WebSocket URL 패턴 설정 완료')
