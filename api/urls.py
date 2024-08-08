from django.urls import path, include
from .bom.bom_restframework import BomViewSet
from .item.item_rest_framework import ItemViewSet
from .plantation.plantation import PlantationViewSet
from .planpart.planpart import PlanPartViewSet
from .user.user_restframework import UserViewSet
from .order.order_restframework import OrderViewSet
from .util.utils import *
from rest_framework.routers import DefaultRouter
from .flutter.flutter import *
router = DefaultRouter()
router.register(r'bom', BomViewSet)
router.register(r'item', ItemViewSet)
router.register(r'user', UserViewSet)
router.register(r'order', OrderViewSet)
router.register(r'plantation', PlantationViewSet)
router.register(r'planpart', PlanPartViewSet)


urlpatterns = [
    path('', include(router.urls)),

    path('util/user-table-data/', user_table_data),
    path('util/fetch-data/', fetch_data),
    path('flutter/login/', login),
    path('flutter/csrf/', csrf),
    path('flutter/container-map/', container_map),
    path('flutter/container-sen-map/', container_sen_map),

]
