from .views import *
from django.urls import path
urlpatterns = [
    path('alram/contact', alram_contact),
    path('alram/control', alram_control),
    path('alram/etc', alram_etc),
    path('alram/plan', alram_plan),

    path('register/register', register_register),
    path('register/select', register_select),

    path('breakdown/control', breakdown_control),
    path('breakdown/collect', breakdown_collect),

    path('harvest/faq', harvest_faq),
    path('harvest/info', harvest_info),
    path('harvest/manual', harvest_manual),

    path('landing/user', landing_user),
    path('', landing_admin),

    path('manage/auto', manage_auto),

    path('order/build', order_build),
    path('order/delivery', order_delivery),
    path('order/item', order_item),

    path('user/manage', user_manage),
    path('user/part', user_part),

    path('device/control', device_control),
    path('device/explain', device_explain),
]
