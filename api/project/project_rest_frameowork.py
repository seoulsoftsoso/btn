from datetime import datetime, timedelta
from rest_framework import viewsets
from api.models import script, EntScript, UserMaster, BomMaster, Plantation, Manual
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import serializers
from django.db import transaction
from rest_framework.response import Response
from rest_framework.decorators import action


class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = EntScript
        fields = '__all__'
        extra_kwargs = {
            'delete_flag': {'required': False},
        }
        read_only_fields = ['id']

    def get_by_user(self):
        return UserMaster.objects.get(user=self.context['request'].user)
    
    def create(self, instance):
        instance['created_by'] = self.get_by_user()
        instance['updated_by'] = self.get_by_user()
        instance['delete_flag'] = 'N'

        return super().create(instance)

    def update(self, instance, validated_data):
        return super().update(instance, validated_data)

    def delete (self, instance):
        instance['delete_flag'] = 'Y'
        return super().update(instance)
    

class ProjectViewSet(viewsets.ModelViewSet):

    queryset = EntScript.objects.all()
    serializer_class = ProjectSerializer
    http_method_names = ['get', 'post', 'patch', 'delete']
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['date', 'done_flag', "entManual"]
    read_only_fields = ['id']
    permission_classes = []

    def get_queryset(self):
        ret = EntScript.objects.filter(delete_flag='N').prefetch_related('created_by', 'updated_by')
        user_id = self.request.query_params.get('user_id')
        if user_id:
            ret = ret.filter(created_by__user_id=user_id)
        if self.request.query_params.get('fr_date'):
            ret = ret.filter(date__gte=self.request.query_params.get('fr_date'))
        if self.request.query_params.get('to_date'):
            ret = ret.filter(date__lte=self.request.query_params.get('to_date'))
        if self.request.query_params.get('container_id'):
            ret = ret.filter(plantation__bom_id=self.request.query_params.get('container_id'))
        return ret    
    
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
    
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)
    
    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        with transaction.atomic():
            instance.delete_flag = 'Y' 
            instance.save()
        return Response({'message': 'success'})
