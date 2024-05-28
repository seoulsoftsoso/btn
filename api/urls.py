from django.urls import path
from .bom.bom import *
from .item.item import *
from .order.order import *
from .user.user import *
from .util.utils import *

urlpatterns = [
    path('bom/list', bom_list),
    path('bom/add/<int:order>', bom_add),
    path('bom/edit/<int:bom_id>', bom_edit),
    path('bom/delete/<int:bom_id>', bom_delete),

    path('item/list', item_list),
    path('item/add', item_add),
    path('item/edit/<int:item_id>', item_edit),
    path('item/delete/<int:item_id>', item_delete),

    path('order/list', order_list),
    path('order/add', order_add),
    path('order/edit/<int:orer_id>', order_edit),
    path('order/delete/<int:order_id>', order_delete),

    path('user/list', user_list),
    path('user/add', user_add),
    path('user/edit/<int:user_id>', user_edit),
    path('user/delete/<int:user_id>', user_delete),

    path('util/user-table-data/', user_table_data),

]
