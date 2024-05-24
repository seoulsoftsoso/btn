from django.urls import re_path
import logging
from button.ws import consumers

logger = logging.getLogger(__name__)

websocket_urlpatterns = [
    re_path(r'ws/landing/user/$', consumers.DashboardConsumer.as_asgi()),
]
logger.info('WebSocket URL 패턴 설정 완료')
