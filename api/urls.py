from django.urls import path
from .bom.bom import *
from .item.item import *
from .order.order import *
from .user.user import *

urlpatterns = [
    path('bom/list', bom_list),
    path('bom/add', bom_add),
    path('bom/edit/<int:id>', bom_edit),
    path('bom/delete/<int:id>', bom_delete),

    path('items/list', item_list),
    path('items/add', item_add),
    path('items/edit/<int:id>', item_edit),
    path('items/delete/<int:id>', item_delete),

    path('order/list', order_list),
    path('order/add', order_add),
    path('order/edit/<int:id>', order_edit),
    path('order/delete/<int:id>', order_delete),

    path('user/list', user_list),
    path('user/add', user_add),
    path('user/edit/<int:id>', user_edit),
    path('user/delete/<int:id>', user_delete),
]
