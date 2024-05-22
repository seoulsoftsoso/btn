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
        if password != confirm_password:
            return render(request, "register/register.html", {"error": "비밀번호가 일치하지 않습니다."})
        user = User.objects.create_user(username=user_id, password=password, email=email)
        created_user = request.user if request.user.id is not None else user
        current_user = UserMaster.objects.create(user=user, created_by= created_user, updated_by= created_user, user_code=license_code,user_name= user_name, tel=tel, address=address, signature=signature)
        data = {}
        data['licensee_no'] = license_code
        data['owner_name'] = user_name
        data['charge_name'] = company_name
        data['charge_tel'] = tel
        data['created_by'] = created_user
        data['updated_by'] = created_user
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
        ).values()
    return JsonResponse(list(users.values()), safe=False)

def user_edit(request):
    user = UserMaster.objects.get(id = request.POST['id'])
    user.email = request.POST['email']
    user.save()
    return JsonResponse({'status': 'success'})

def user_delete(request, id):
    user = UserMaster.objects.get(id=id)
    user.delete()
    return JsonResponse({'status': 'success'})

