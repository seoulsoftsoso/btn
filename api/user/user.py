from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth import login
from django.db.models import F
from django.contrib.auth.models import User
from api.models import UserMaster, EnterpriseMaster
def user_add(request):
    if request.method == "POST":
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        email = request.POST.get('email')
        user_id= email[:email.find("@")]
        user_name = request.POST.get('user_name')
        company_name = request.POST.get('company_name')
        license_code = request.POST.get('license_code')
        tel = request.POST.get('tel')
        signature = request.POST.get('signature')
        address = request.POST.get('address')
        charge_name= request.POST.get('charge_name')
        charge_tel = request.POST.get('charge_tel')
        charge_pos = request.POST.get('charge_pos')
        if password != confirm_password:
            return render(request, "register/register.html", {"error": "비밀번호가 일치하지 않습니다."})
        user = User.objects.create_user(username=user_id, password=password, email=email)
        current_user = UserMaster.objects.create(user=user, user_code=license_code,user_name= user_name, tel=tel, address=address, signature=signature, delete_flag='N')
        data = {}
        data['licensee_no'] = license_code
        data['owner_name'] = user_name
        data['charge_name'] = charge_name
        data['customer_name'] = company_name
        data['charge_pos'] = charge_pos
        data['charge_tel'] = charge_tel
        data['delete_flag'] = 'N'
        ent = EnterpriseMaster.objects.create(
            **data
        )
        current_user.ent = ent
        current_user.save()
        if request.user.id is not None:
            return JsonResponse({"status": "success"})
        login(request, user)
        return redirect("dashboard")
    return render(request, "register/register.html")

def user_list(request):
    users = UserMaster.objects.all().annotate(
        email = F('user__email'),
        license_code = F('ent__licensee_no'),
        owner_name = F('ent__owner_name'),
        company_name = F('ent__customer_name'),
        charge_name = F('ent__charge_name'),
        charge_pos = F('ent__charge_pos'),
        charge_tel= F('ent__charge_tel')
        ).values().filter(delete_flag='N')
    return JsonResponse(list(users.values()), safe=False)

def user_edit(request, id):
    user = UserMaster.objects.get(id=id)
    user.ent.owner_name = request.POST['owner_name']
    user.tel = request.POST['tel']
    user.signature = request.POST['signature']
    user.address = request.POST['address']
    user.ent.customer_name = request.POST['company_name']
    user.ent.licensee_no = request.POST['license_code']
    user.ent.charge_tel = request.POST['charge_tel']
    user.ent.charge_name = request.POST['charge_name']
    user.ent.charge_pos = request.POST['charge_pos']
    user.ent.save()
    user.save()
    return JsonResponse({'status': 'success'})

def user_delete(request, id):
    user = UserMaster.objects.get(id=id)
    user.delete_flag = "N"
    user.save()
    return JsonResponse({'status': 'success'})

