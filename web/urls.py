from .views import *
from django.urls import path
urlpatterns = [
    # 알람
    path('alram/contact', alram_contact),
    path('alram/control', alram_control),
    path('alram/etc', alram_etc),
    path('alram/plan', alram_plan),

    # 유저 등록
    path('register/register', register_register),
    path('register/select', register_select),

    # 고장 관리
    path('breakdown/control', breakdown_control),
    path('breakdown/collect', breakdown_collect),

    # 재배 관리
    path('harvest/faq', harvest_faq),
    path('harvest/info', harvest_info),
    path('harvest/manual', harvest_manual),

    # 초기 화면
    path('landing/user', landing_user),
    path('landing/user/graph/all', landing_user_graph_all),
    path('landing/user/graph/single', landing_user_graph_all),
    path('', landing_admin),

    # 자동 재배 관리
    path('manage/auto', manage_auto),

    # 주문 관리
    path('order/build', order_build),
    path('order/delivery', order_delivery),
    path('order/item', order_item),

    # 유저 관리
    path('user/manage', user_manage),
    path('user/part', user_part),

    # 장치 관리
    path('device/control', device_control),
    path('device/explain', device_explain),
]
