from rest_framework import viewsets
from api.models import OrderMaster, ItemMaster, UserMaster, OrderProduct, BomMaster
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import serializers
from django.db import transaction
from rest_framework.response import Response
import uuid, json

from api.user.user_restframework import ClientSerializer


class OrderMasterSerializer(serializers.ModelSerializer):
    client = ClientSerializer()
    class Meta:
        model = OrderMaster
        fields = '__all__'
        extra_kwargs = {
            'delete_flag': {'required': False},
            'created_by': {'required': False},
            'updated_by': {'required': False},
            'comment': {'required': False},
        }
        read_only_fields = ['id']




class OrderViewSet(viewsets.ModelViewSet):

    queryset = OrderMaster.objects.all()
    serializer_class = OrderMasterSerializer
    http_method_names = ['get', 'post', 'patch', 'delete']
    filter_backends = [DjangoFilterBackend]
    read_only_fields = ['id']
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return OrderMaster.objects.filter(delete_flag='N')

    def create(self, request, *args, **kwargs):
        User = UserMaster.objects.get(user_id=request.user.id)
        request.data._mutable = True
        so_no = str(uuid.uuid4())
        request.data['so_no'] = so_no
        request.data['created_by'] = User.id
        request.data['updated_by'] = User.id
        request.data['delete_flag'] = 'N'
        request.data._mutable = False
        order = super().create(request, request, *args, **kwargs)
        container = ItemMaster.objects.get(
            created_by=User,
            level=0)
        for i in range(0, int(request.data['order_cnt'])):
            op = OrderProduct.objects.create(
                unique_no=str(uuid.uuid4()),
                product_name=container.item_name,
                order_id=order.data['id'],
                delete_flag='N',
                op_cnt=1,
                status=1,
                created_by=User,
                updated_by=User,
            )
            bom = BomMaster.objects.create(
                level=0,
                part_code=container.item_name,
                item=container,
                order_cnt=1,
                total=container.standard_price,
                tax=container.standard_price * 0.1,
                op=op,
                delete_flag='N',
                created_by=User,
                updated_by=User,
                order_id=order.data['id'],
            )
            op.bom = bom
            op.save()
        return Response({'message': 'success'})

    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        with transaction.atomic():
            isinstance.delete_flag = 'Y'
            instance.save()
        return Response({'message': 'success'})
