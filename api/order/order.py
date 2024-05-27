import json
import uuid

from django.db.models import F
from django.http import JsonResponse

from api.models import OrderMaster, UserMaster, OrderProduct, ItemMaster, BomMaster


def order_list(request):
    if request.user.id is None:
        return JsonResponse({'message': 'login required', 'data': []})
    orders = OrderMaster.objects.annotate(avatar=F('client__signature'), full_name=F('client__user_name'),
                                          post=F('client__tel'), ).filter(delete_flag='N').values()
    return JsonResponse({'data': list(orders.values())})


def order_add(request):
    if request.user.id is None:
        return JsonResponse({'message': 'login required', 'data': []})
    order = request.POST.dict()
    so_no = str(uuid.uuid4())
    order['client'] = json.loads(order['client'])
    order['client'] = order['client'][0]['value']
    qty = int(order['order_cnt'])
    user = UserMaster.objects.get(user_id = request.user.id)
    order = OrderMaster.objects.create(so_no=so_no, client=UserMaster.objects.get(id=order['client']),
                               order_date=order['order_date'], order_cnt=order['order_cnt'], order_price=order['order_price'],
                               order_tax=order['order_tax'], order_place=order['order_place'],
                               order_total=order['order_total'], comment=order['order_comment'], delete_flag='N',
                               created_by=user, updated_by=user)
    for i in range(0, qty):
        container = ItemMaster.objects.get(created_by = user, level = 0)
        op = OrderProduct.objects.create(unique_no=str(uuid.uuid4()),
                                                product_name=container.item_name, order=order,
                                                delete_flag='N', op_cnt=1, status=1, created_by=user, updated_by=user)
        bom = BomMaster.objects.create(level=0, part_code=container.item_name, item=container,
                                       order_cnt=1, total=container.standard_price, tax=container.standard_price*0.1,
                                       op=op, delete_flag='N', created_by=user, updated_by=user, order = order)
        op.bom = bom
        op.save()
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
