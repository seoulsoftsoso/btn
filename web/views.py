from django.shortcuts import render
from button.ws.mongo_updates import start_listening_to_changes
# 알람

def alram_contact(request):
    return render(request, 'alram/contact.html')

def alram_control(request):
    return render(request, 'alram/control.html')

def alram_etc(request):
    return render(request, 'alram/etc.html')

def alram_plan(request):
    return render(request, 'alram/plan.html')

# 유저 관리

def register_register(request):
    return render(request, 'register/register.html')

def register_select(request):
    return render(request, 'register/select.html')

# 고장 관리

def breakdown_control(request):
    return render(request, 'breakdown/control.html')   

def breakdown_collect(request):
    return render(request, 'breakdown/collect.html')

# 재배 관리

def harvest_faq(request):
    return render(request, 'harvest/faq.html')

def harvest_info(request):
    return render(request, 'harvest/info.html')

def harvest_manual(request):
    return render(request, 'harvest/manual.html')

# 초기 화면

def landing_user(request):
    start_listening_to_changes(request)
    return render(request, 'landing/dashboard2.html')
def landing_user_graph_all(request):
    return render(request, 'landing/user_graphAll.html')
def landing_user_graph_single(request):
    return render(request, 'landing/user_graphSingle.html')
def landing_admin(request):
    return render(request, 'landing/dashboard.html')

# 자동 재배 관리

def manage_auto(request):
    return render(request, 'manage/auto.html')

# 주문 관리

def order_build(request):
    return render(request, 'order/build.html')

def order_delivery(request):
    return render(request, 'order/delivery.html')

def order_item(request):
    return render(request, 'order/item.html')

# 유저 관리

def user_manage(request):
    return render(request, 'user/manage.html')

def user_part(request):
    return render(request, 'user/part.html')

def device_control(request):
    return render(request, 'device/control.html')

def device_explain(request):
    return render(request, 'device/explain.html')

