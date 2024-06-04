from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action
from api.models import BomMaster, ItemMaster, OrderProduct, UserMaster
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from datetime import datetime
from api.item.item_rest_framework import ItemSerializer
import uuid
import json


class BomMasterSerializer(serializers.ModelSerializer):
    item_price = serializers.FloatField(source='item.standard_price', read_only=True)
    product_info = serializers.CharField(source='item.item_name', read_only=True)
    image = serializers.CharField(source='item.brand', read_only=True)
    product_name = serializers.CharField(source='item.item_name', read_only=True)
    created_by = serializers.CharField(required=False, read_only=True)  # 최종작성일
    updated_by = serializers.CharField(required=False, read_only=True)  # 최종작성자
    delete_flag = serializers.CharField(required=False, read_only=True)  # 삭제여부

    class Meta:
        model = BomMaster
        fields = ['id', 'part_code', 'item_id', 'order_cnt', 'total', 'tax', 'order_id', 'parent_id', 'level', 'created_by', 'updated_by', 'delete_flag', 'item_price', 'product_info', 'image', 'product_name', 'parent', 'op']


    def create(self, instance):
        instance['created_by'] = self.get_by_username()
        instance['updated_by'] = self.get_by_username()
        instance['delete_flag'] = 'N'

        return super().create(instance)

    def update(self, instance, validated_data):
        validated_data['updated_by'] = self.get_by_username()

        return super().update(instance, validated_data)

    def delete(self, instance):
        instance['delete_flag'] = 'Y'
        return super().update(instance)


class BomCreateSerializer(serializers.ModelSerializer):
    created_by = serializers.StringRelatedField(read_only=True)
    updated_by = serializers.StringRelatedField(read_only=True)
    class Meta:
        model = BomMaster
        fields = '__all__'

    def get_by_username(self):
        User = UserMaster.objects.get(user_id=self.context['request'].user.id)
        return User.id

    def create(self, instance):
        instance['created_by_id'] = self.get_by_username()

        instance['updated_by_id'] = self.get_by_username()


        return super().create(instance)

    def update(self, instance, validated_data):
        validated_data['updated_by'] = self.get_by_username()

        return super().update(instance, validated_data)


class BomViewSet(viewsets.ModelViewSet):
    queryset = BomMaster.objects.filter(delete_flag='N')
    serializer_class = BomMasterSerializer
    http_method_names = ['get', 'post', 'patch', 'delete']
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['order']
    read_only_fields = ['id']
    permission_classes = [IsAuthenticated]


    def get_queryset(self):
        qs = BomMaster.objects.filter(delete_flag='N')
        return qs

    def create(self, request, *args, **kwargs):
        rawData = request.data
        item = get_object_or_404(ItemMaster, id=rawData['item_id'])
        order_cnt = int(rawData['order_cnt'])
        parent = rawData.get('parent', '#')
        parent_op_id = None
        level = 0
        if parent and parent != '#':
            parent_bom = get_object_or_404(BomMaster, id=parent)
            parent_op_id = parent_bom.op.id
            level = parent_bom.level + 1
        user = UserMaster.objects.get(user_id=request.user.id)
        boms = []
        for i in range(0, order_cnt):
            bom = BomMaster.objects.create(
                part_code=rawData.get('text', ''),
                item_id=rawData['item_id'],
                order_cnt=1,
                total = item.standard_price,
                tax = item.standard_price * 0.1,
                order_id=rawData['order_id'],
                parent_id=parent,
                level=level,
                delete_flag='N',
                created_by=user,
                updated_by=user,
                op_id = parent_op_id
            )
            boms.append(bom.id)
            if level == 0:
                op = OrderProduct.objects.create(
                    unique_no=str(uuid.uuid4()),
                    product_name=item.item_name,
                    order_id=rawData['order_id'],
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
                bom.save()
        return Response({'message': 'success', 'boms': boms}, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['patch'])
    def edit_order_count(self, request, *args, **kwargs):
        bom_id = kwargs.get('pk')
        bom = get_object_or_404(BomMaster, id=bom_id)
        data = request.data
        order_cnt = int(data['order_cnt'])
        item_totalPrice = bom.item.standard_price * order_cnt
        orderProduct = OrderProduct.objects.get(id=bom.op_id)
        bomEditData = {
            'order_cnt': order_cnt,
            'total': item_totalPrice,
            'tax': item_totalPrice * 0.1
        }
        bom.__dict__.update(bomEditData)
        orderProduct.save()
        return Response({'message': 'success'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['patch'])
    def edit_part_code(self, request, *args, **kwargs):
        bom_id = kwargs.get('pk')
        bom = get_object_or_404(BomMaster, id=bom_id)
        data = request.data
        bom.part_code = data['part_code']
        bom.save()
        return Response({'message': 'success'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['delete'])
    def delete_bom(self, request, pk=None):
        bom = get_object_or_404(BomMaster, id=pk)
        queue = [bom]
        while queue:
            current = queue.pop()
            current.delete_flag = 'Y'
            current.save()
            try:
                order_product = OrderProduct.objects.get(id=current.op_id)
                order_product.delete_flag = 'Y'
                order_product.save()
            except OrderProduct.DoesNotExist:
                pass
            children = BomMaster.objects.filter(parent_id=current.id)
            for child in children:
                queue.append(child)
        return Response({'message': 'success'}, status=status.HTTP_200_OK)
