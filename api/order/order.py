import json
import uuid

from django.db.models import F
from django.http import JsonResponse

from api.models import OrderMaster, UserMaster, ItemMaster, BomMaster, OrderProduct

from api.bom.bom import bom_add
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

def format_order_data(orderData):
    return {
        'client_id': orderData['client'],
        'order_date': orderData['order_date'],
        'order_cnt': orderData['order_cnt'],
        'order_price': orderData['order_price'],
        'order_total': orderData['order_total'],
        'order_tax': orderData['order_tax'],
        'order_place': orderData['order_place'],
        'comment': orderData['comment'],
    }

def order_list(request):
    if request.user.id is None:
        return JsonResponse({'message': 'login required', 'data': []})
    orders = OrderMaster.objects.annotate(avatar=F('client__signature'), full_name=F('client__user_name'),
                                          post=F('client__tel'), ).filter(delete_flag='N').values()
    return JsonResponse({'data': list(orders.values())})


@csrf_exempt
@require_POST
def order_add(request):
    if request.user.id is None:
        return JsonResponse({'message': 'login required', 'data': []})
    RawOrderData = request.POST.dict()
    so_no = str(uuid.uuid4())
    Client = RawOrderData['client']
    RawOrderData['client'] = json.loads(Client)[0]['value']
    qty = int(RawOrderData['order_cnt'])
    User = UserMaster.objects.get(user_id = request.user.id)
    order = OrderMaster.objects.create(
                                so_no=so_no,
                                **format_order_data(RawOrderData),
                                delete_flag='N',
                                created_by=User, updated_by=User)
    for i in range(0, qty):
        container = ItemMaster.objects.get(created_by=User, level=0)
        op = OrderProduct.objects.create(unique_no=str(uuid.uuid4()),
                                         product_name=container.item_name, order=order,
                                         delete_flag='N', op_cnt=1, status=1, created_by=User, updated_by=User)
        bom = BomMaster.objects.create(level=0, part_code=container.item_name, item=container,
                                       order_cnt=1, total=container.standard_price, tax=container.standard_price * 0.1,
                                       op=op, delete_flag='N', created_by=User, updated_by=User, order=order)
        op.bom = bom
        bom.save()
    return JsonResponse({'message': 'success'})

@csrf_exempt
@require_POST
def order_edit(request, order_id):
    data = request.POST.dict()
    order = OrderMaster.objects.get(id=order_id)
    orderData = format_order_data(data)
    order.__dict__.update(orderData)
    order.save()
    return JsonResponse({'message': 'success'})

@csrf_exempt
@require_POST
def order_delete(request, order_id):
    order = OrderMaster.objects.get(id=order_id)
    order.delete_flag = 'Y'
    order.save()
    return JsonResponse({'message': 'success'})
