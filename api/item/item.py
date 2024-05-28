from django.http import JsonResponse
from api.models import ItemMaster, UserMaster
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

@csrf_exempt
@require_POST
def format_item_data(itemData):
    return {
        'item_code': itemData['item_code'],
        'item_name': itemData['item_name'],
        'item_type': itemData['item_type'],
        'specification': itemData['specification'],
        'model': itemData['model'],
        'brand': itemData['brand'],
        'level': itemData['level'],
        'standard_price': itemData['standard_price'],
    }

def item_list(request):
    if request.user.id is None:
        return JsonResponse({'message': 'login required', 'data': []})
    items = ItemMaster.objects.filter(delete_flag='N').values()
    return JsonResponse({'data': list(items.values())})

@csrf_exempt
@require_POST
def item_add(request):
    item = request.POST.dict()
    user = UserMaster.objects.get(user_id = request.user.id)
    addItemData = format_item_data(item)

    ItemMaster.objects.create(
        **addItemData,
        delete_flag='N',
        created_by=user,
        updated_by=user
    )
    return JsonResponse({'message': 'success'})

@csrf_exempt
@require_POST
def item_edit(request, item_id):
    ItemEditData = request.POST.dict()
    item = ItemMaster.objects.get(id=item_id)
    itemData = format_item_data(ItemEditData)
    item.__dict__.update(itemData)
    item.save()
    return JsonResponse({'message': 'success'})


def item_delete(request, id):
    item = ItemMaster.objects.get(id=id)
    item.delete_flag = 'Y'
    item.save()
    return JsonResponse({'message': 'success'})
