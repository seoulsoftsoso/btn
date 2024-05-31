from rest_framework import viewsets
from api.models import ItemMaster
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import serializers
from django.db import transaction
from rest_framework.response import Response


class ItemSerializer(serializers.ModelSerializer):
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = ItemMaster
        fields = '__all__'
        extra_kwargs = {
            'delete_flag': {'required': False},
        }
        read_only_fields = ['id']


class ItemViewSet(viewsets.ModelViewSet):

    queryset = ItemMaster.objects.all()
    serializer_class = ItemSerializer
    http_method_names = ['get', 'post', 'patch', 'delete']
    filter_backends = [DjangoFilterBackend]
    read_only_fields = ['id']
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ItemMaster.objects.filter(delete_flag='N').prefetch_related('created_by', 'updated_by')

    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        with transaction.atomic():
            isinstance.delete_flag = 'Y'
            instance.save()
        return Response({'message': 'success'})

