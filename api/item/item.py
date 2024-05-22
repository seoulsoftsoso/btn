from django.http import JsonResponse
from api.models import ItemMaster


def item_list(request):
    if request.user.id is None:
        return JsonResponse({'message': 'login required', 'data': []})
    items = ItemMaster.objects.filter(delete_flag='N').values()
    return JsonResponse({'data': list(items.values())})


def item_add(request):
    item = request.POST.dict()
    ItemMaster.objects.create(
        item_code=item['code'],
        item_name=item['name'],
        item_type=item['type'],
        specification=item['specification'],
        model=item['model'],
        brand=item['brand'],
        level=item['level'],
        standard_price=item['standard_price'],
        delete_flag='N',
        created_by=request.user,
        updated_by=request.user
    )
    return JsonResponse({'message': 'success'})


def item_edit(request, id):
    data = request.POST.dict()
    item = ItemMaster.objects.get(id=id)
    item.item_code = data['item_code']
    item.item_name = data['item_name']
    item.item_type = data['item_type']
    item.specification = data['specification']
    item.model = data['model']
    item.brand = data['brand']
    item.level = data['level']
    item.standard_price = data['standard_price']
    item.save()
    return JsonResponse({'message': 'success'})


def item_delete(request, id):
    item = ItemMaster.objects.get(id=id)
    item.delete_flag = 'Y'
    item.save()
    return JsonResponse({'message': 'success'})
