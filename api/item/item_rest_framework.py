from rest_framework import viewsets
from api.models import ItemMaster, UserMaster
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import serializers
from django.db import transaction
from rest_framework.response import Response


class ItemSerializer(serializers.ModelSerializer):
    delete_flag = serializers.CharField(required=False, read_only=True)  # 삭제여부
    class Meta:
        model = ItemMaster
        fields = '__all__'
        extra_kwargs = {
            'delete_flag': {'required': False},
        }
        read_only_fields = ['id']

    def create(self, instance):
        instance['created_by'] = UserMaster.objects.get(user=self.context['request'].user)
        instance['updated_by'] = UserMaster.objects.get(user=self.context['request'].user)
        instance['delete_flag'] = 'N'

        return super().create(instance)

    def update(self, instance, validated_data):
        validated_data['updated_by'] = UserMaster.objects.get(user=self.context['request'].user)
        return super().update(instance, validated_data)

    def delete (self, instance):
        instance['delete_flag'] = 'Y'
        return super().update(instance)


class ItemViewSet(viewsets.ModelViewSet):

    queryset = ItemMaster.objects.all()
    serializer_class = ItemSerializer
    http_method_names = ['get', 'post', 'patch', 'delete']
    filter_backends = [DjangoFilterBackend]
    read_only_fields = ['id']
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ItemMaster.objects.filter(delete_flag='N')

    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)
    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        with transaction.atomic():
            isinstance.delete_flag = 'Y'
            instance.save()
        return Response({'message': 'success'})

