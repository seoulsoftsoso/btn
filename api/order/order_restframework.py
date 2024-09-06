from rest_framework import viewsets
from rest_framework.decorators import action

from api.models import OrderMaster, ItemMaster, UserMaster, OrderProduct, BomMaster, Plantation, PlanPart
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import serializers
from django.db import transaction
from rest_framework.response import Response
import uuid

from api.user.user_restframework import ClientSerializer


class OrderMasterSerializer(serializers.ModelSerializer):
    delete_flag = serializers.CharField(required=False, read_only=True)  # 삭제여부

    class Meta:
        model = OrderMaster
        fields = '__all__'
        extra_kwargs = {
            'created_by': {'required': False},
            'updated_by': {'required': False},
            'comment': {'required': False},
        }
        read_only_fields = ['id']

    def create(self, validated_data):
        User = UserMaster.objects.get(user_id=self.context['request'].user.id)
        validated_data['created_by'] = User
        validated_data['updated_by'] = User
        validated_data['delete_flag'] = 'N'
        return super().create(validated_data)

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret['client'] = ClientSerializer(instance.client).data
        return ret

    def delete(self, instance):
        instance['delete_flag'] = 'Y'
        return super().update(instance)


class OrderViewSet(viewsets.ModelViewSet):
    queryset = OrderMaster.objects.all()
    serializer_class = OrderMasterSerializer
    http_method_names = ['get', 'post', 'patch', 'delete']
    filter_backends = [DjangoFilterBackend]
    read_only_fields = ['id']
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return OrderMaster.objects.filter(delete_flag='N').order_by('-id')

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

    @action(methods=['post'], detail=True)
    def reg_container(self, request, *args, **kwargs):
        order = self.get_object()
        sensor_by_order = BomMaster.objects.filter(order=order, level=2, delete_flag='N')
        container_by_order = BomMaster.objects.filter(order=order, level=0, delete_flag='N')
        user = UserMaster.objects.get(user_id=request.user.id)
        for container in container_by_order:
            item_by_container = container.item
            Plantation.objects.create(
                c_code=container.part_code,
                c_name=item_by_container.item_name,
                owner=order.client,
                bom=container,
                reg_flag='Y',
                created_by=user,
                updated_by=user,
            )
        for sensor in sensor_by_order:
            controller = sensor.parent
            container_id = controller.parent_id
            plantation_id = Plantation.objects.get(bom_id = container_id).id
            PlanPart.objects.create(
                p_name = sensor.part_code,
                part = sensor,
                plantation_id = plantation_id,
                delete_flag = 'N',
                reg_flag = 'N',
                message = "init",
                status = "WAIT_CON",
                type=sensor.item.item_type,
                created_by = user,
                updated_by = user
            )
        order.comment = "주문완료"
        order.save()

        return Response({'message': 'success'})

    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        with transaction.atomic():
            isinstance.delete_flag = 'Y'
            instance.save()
        return Response({'message': 'success'})
