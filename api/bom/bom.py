from django.http import JsonResponse
from api.models import BomMaster, ItemMaster, OrderProduct, UserMaster
from datetime import datetime
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import F, FloatField
from django.db.models.functions import Cast, Round
import json
import uuid
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

def format_bom_data(bomData):
    return {
        'part_code': bomData['product_name'],
        'item_id': bomData['item_id'],
        'order_cnt': bomData['order_cnt'],
    }

def bom_list(request):
    order = request.GET.get('order')
    bomTree = list(BomMaster.objects.filter(delete_flag='N', order_id=order).annotate(
        item_price=Round(Cast(F('item__standard_price'), FloatField()), 2),
        product_info=F('item__item_name'),
        image=F('item__brand'),
        product_name=F('item__item_name'),
    ).values('id', 'product_name', 'order_cnt', 'item_price', 'product_info', 'image', 'level', 'item_id', 'parent',
             'part_code'))
    return JsonResponse(bomTree, safe=False)

@csrf_exempt
@require_POST
def bom_add(request, order):
    RawTreeData = json.loads(request.body)
    RawBomData = RawTreeData['data']
    ItemData = ItemMaster.objects.get(id=RawBomData['item_id'])
    user = UserMaster.objects.get(user_id=request.user.id)
    order_cnt = int(RawBomData['order_cnt'])
    if RawTreeData['parent'] == '#':
        RawTreeData['parent'] = None
    else:
        bom = BomMaster.objects.filter(id=RawTreeData['parent']).first()
        level = bom.level + 1
    total = ItemData.standard_price * order_cnt
    bomPriceData  ={
        'total': total,
        'tax': total * 0.1
    }
    boms = []
    if level == 3:
        bom = BomMaster.objects.create(
            **format_bom_data(RawBomData),
            **bomPriceData,
            order_id = order,
            parent_id=RawTreeData['parent'],
            level = level,
            delete_flag='N',
            created_by=user,
            updated_by=user
        )
        boms.append(bom.id)
        return JsonResponse({'message': 'success', 'boms': boms})
    else:
        for i in range(0, order_cnt):
            bom = BomMaster.objects.create(
                **format_bom_data(RawBomData),
                **bomPriceData,
                order_id = order,
                parent_id=RawTreeData['parent'],
                level=level,
                delete_flag='N',
                created_by=user,
                updated_by=user
            )
            boms.append(bom.id)
            if level == 1:
                op = OrderProduct.objects.create(
                    unique_no=str(uuid.uuid4()),
                    product_name=ItemData.item_name,
                    order_id=order,
                    delivery_date=datetime.now(),
                    op_cnt=order_cnt,
                    delivery_addr='HCM',
                    request_note='Test',
                    status='1',
                    delete_flag='N',
                    bom=bom,
                    created_by=user,
                    updated_by=user
                )
                bom.op = op
            bom.order_id = order
            bom.save()
        return JsonResponse({'message': 'success', 'boms': boms})

@csrf_exempt
@require_POST
def bom_edit(request, bom_id):
    rawBomData = request.POST.dict()
    bom = BomMaster.objects.get(id=bom_id)
    try:
        order_cnt = int(rawBomData['order_cnt'])
        item_totalPrice = bom.item.standard_price * order_cnt
        orderProduct = OrderProduct.objects.get(id=bom.op_id)
        bomEditData = {
            'order_cnt': order_cnt,
            'total': item_totalPrice,
            'tax': item_totalPrice * 0.1
        }
        bom.__dict__.update(bomEditData)
        orderProduct.save()
    except:
        pass
    try:
        bom.part_code = rawBomData['part_code']
        bom.save()
    except:
        pass
    return JsonResponse({'message': 'success'})

@csrf_exempt
@require_POST
def bom_delete(request, bom_id):
    bom = BomMaster.objects.get(id=bom_id)
    queue = [bom]
    while queue:
        current = queue.pop()
        current.delete_flag = 'Y'
        current.save()
        try:
            orderProduct = OrderProduct.objects.get(id=current.op_id)
            orderProduct.delete_flag = 'Y'
            orderProduct.save()
        except:
            pass
        children = BomMaster.objects.filter(parent_id=current.id)
        for child in children:
            queue.append(child)
    return JsonResponse({'message': 'success'})
