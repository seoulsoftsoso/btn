import json
import uuid

from django.db.models import F
from django.http import JsonResponse

from api.models import OrderMaster, UserMaster


def order_list(request):
    if request.user.id is None:
        return JsonResponse({'message': 'login required', 'data': []})
    orders = OrderMaster.objects.annotate(avatar=F('client__signature'), full_name=F('client__user__username'),
                                          post=F('client__tel'), ).filter(delete_flag='N').values()
    return JsonResponse({'data': list(orders.values())})


def order_add(request):
    if request.user.id is None:
        return JsonResponse({'message': 'login required', 'data': []})
    order = request.POST.dict()
    so_no = str(uuid.uuid4())
    order['client'] = json.loads(order['client'])
    order['client'] = order['client'][0]['value']
    OrderMaster.objects.create(so_no=so_no, place=order['order_place'], client=UserMaster.objects.get(id=order['client']),
                               order_date=order['order_date'], order_cnt=order['order_cnt'], order_price=order['order_price'],
                               order_tax=order['order_tax'], order_place=order['order_place'],
                               order_total=order['order_total'], comment=order['order_comment'], delete_flag='N',
                               created_by=request.user,
                               updated_by=request.user)
    return JsonResponse({'message': 'success'})


def order_edit(request, id):
    data = request.POST.dict()
    order = OrderMaster.objects.get(id=id)
    for key in data:
        order.__dict__[key] = data[key]
    order.save()
    return JsonResponse({'message': 'success'})


def order_delete(request, id):
    order = OrderMaster.objects.get(id=id)
    order.delete_flag = 'Y'
    order.save()
    return JsonResponse({'message': 'success'})
