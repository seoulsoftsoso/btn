from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth import login
from django.db.models import F
from django.contrib.auth.models import User
from api.models import UserMaster, EnterpriseMaster
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST


def format_data(data):
    return {
        'user': format_user_data(data),
        'ent': format_ent_data(data)
    }
def format_user_data(userData):
    return {
        'user_code': userData['license_code'],
        'user_name': userData['user_name'],
        'tel': userData['tel'],
        'address': userData['address'],
        'signature': userData['signature'],
        'email': userData['email'],
        'password': userData['password'],
        'confirm_password': userData['confirm_password'],
    }

def format_ent_data(entData):
    return {
        'licensee_no': entData['license_code'],
        'owner_name': entData['user_name'],
        'charge_name': entData['charge_name'],
        'customer_name': entData['company_name'],
        'charge_pos': entData['charge_pos'],
        'charge_tel': entData['charge_tel'],
    }
@csrf_exempt
@require_POST
def user_add(request):
    if request.method == "POST":
        rawData = request.POST.dict()

        if rawData['password'] != rawData['confirm_password']:
            return render(request, "register/register.html", {"error": "비밀번호가 일치하지 않습니다."})

        rawFormattedData = format_data(rawData)

        rawUser = rawFormattedData['user']
        rawEnt = rawFormattedData['ent']

        user = User.objects.create_user(user_name=rawUser['user_name'], email=rawUser['email'], password=rawUser['password'])

        createdUser = UserMaster.objects.create(
            **rawUser,
            user_id = user.id,
            delete_flag='N'
        )

        ent = EnterpriseMaster.objects.create(
            **rawEnt,
            user_id = user.id,
            delete_flag='N'
        )

        createdUser.ent = ent
        createdUser.save()
        if request.user.id is not None:
            return JsonResponse({"status": "success"})

        login(request, user)
        return redirect('home')
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
@csrf_exempt
@require_POST
def user_edit(request, user_id):
    rawUserData = request.POST.dict()
    rawFormattedData = format_data(rawUserData)
    rawUser = rawFormattedData['user']
    rawEnt = rawFormattedData['ent']
    user = UserMaster.objects.get(id=user_id)
    user.__dict__.update(rawUser)
    user.ent.__dict__.update(rawEnt)
    user.ent.save()
    user.save()
    return JsonResponse({'status': 'success'})
@csrf_exempt
@require_POST
def user_delete(request, user_id):
    user = UserMaster.objects.get(id=user_id)
    user.delete_flag = "N"
    user.save()
    return JsonResponse({'status': 'success'})

