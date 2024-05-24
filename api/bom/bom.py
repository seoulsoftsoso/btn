from django.http import JsonResponse
from api.models import BomMaster, ItemMaster, OrderProduct
from datetime import datetime
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import F, FloatField
from django.db.models.functions import Cast, Round
import json
import uuid

def bom_list(request):
    order = request.GET.get('order')
    orderProduct = OrderProduct.objects.filter(order_id=order, delete_flag="N").values_list('id')
    bomTree = list(BomMaster.objects.filter(op_id__in=orderProduct).annotate(
        qty=F('order_cnt'),
        price=Round(Cast(F('item__standard_price'), FloatField()), 2),
        product_info=F('item__item_name'),
        image=F('item__brand'),
        product_name=F('item__item_name'),
    ).values('id', 'part_code', 'qty', 'price', 'product_info', 'image', 'level', 'item_id', 'parent', 'product_name'))
    return JsonResponse(bomTree, safe=False)

def bom_add(request, order):
    request_data = json.loads(request.body)
    product = request_data
    level = 0
    data = product['data']
    item = ItemMaster.objects.get(id=data['item_id'])
    qty = int(data['qty'])
    product['item'] = item
    if product['parent'] == '#':
        product['parent'] = None
    else:
        parent = product['parent']
        bom = BomMaster.objects.filter(id=parent).first()
        product['parent'] = bom
        level = bom.level + 1
    print(level)
    orderData = OrderProduct.objects.create(
        unique_no=str(uuid.uuid4()),
        product_name=item.item_name,
        order_id=order,
        delivery_date=datetime.now(),
        op_cnt=qty,
        delivery_addr='HCM',
        request_note='Test',
        status='1',
        delete_flag='N',
        created_by=request.user,
        updated_by=request.user
    )
    total = item.standard_price * qty
    boms = []
    bom = None
    if level == 2:
        bom = BomMaster.objects.create(
            level=level,
            part_code=item.item_name,
            item=item,
            parent=product['parent'],
            tax=total * 0.1,
            total=total,
            op=orderData,
            order_cnt=qty,
            delete_flag='N',
            created_by=request.user,
            updated_by=request.user
        )
    else:
        for i in range(0, qty):
                bom = BomMaster.objects.create(
                level=level,
                part_code=item.item_name,
                item=item,
                parent=product['parent'],
                tax=total * 0.1,
                total=total,
                op=orderData,
                order_cnt=1,
                delete_flag='N',
                created_by=request.user,
                updated_by=request.user
            )
    orderData.bom = bom
    orderData.save()
    boms.append(bom.id)
    return JsonResponse({'message': 'success', 'order_id': orderData.id, 'boms': boms})


def bom_edit(request,id):
    data = request.POST.dict()
    bom_id = id
    bom = BomMaster.objects.get(id = bom_id)
    try:
        qty = int(data['qty'])
        orderProduct = OrderProduct.objects.get(id=BomMaster.objects.get(id=bom_id).op_id)
        total = bom.item.standard_price * qty
        orderProduct.order_cnt = qty
        bom.total = total
        bom.tax = total * 0.1
        orderProduct.save()
    except:
        pass
    try:
        bom.part_code = data['part_code']
        bom.save()
    except:
        pass
    return JsonResponse({'message': 'success'})


def bom_delete(request):
    if request.method == "POST":
        data = request.POST.dict()
        bom_id = data['id']
        bom = BomMaster.objects.get(id=bom_id)
        queue = [bom]
        while queue:
            current = queue.pop()
            current.delete_flag = 'Y'
            current.save()
            orderProduct = OrderProduct.objects.get(id=current.op_id)
            orderProduct.delete_flag = 'Y'
            orderProduct.save()
            children = BomMaster.objects.filter(parent_id=current.id)
            for child in children:
                queue.append(child)
        return JsonResponse({'message': 'success'})
