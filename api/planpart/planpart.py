from django.db.models import F, Count
from rest_framework import viewsets, status
from rest_framework.decorators import action

from api.models import OrderMaster, ItemMaster, UserMaster, PlanPart, Plantation
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import serializers
from rest_framework.response import Response
import uuid, json



class PlantationSerializer(serializers.ModelSerializer):

    class Meta:
        model = PlanPart
        fields = '__all__'
        extra_kwargs = {
            'created_by': {'required': False},
            'updated_by': {'required': False},
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
        return ret

    def delete(self, instance):
        instance['delete_flag'] = 'Y'
        return super().update(instance)


class PlanPartViewSet(viewsets.ModelViewSet):
    queryset = PlanPart.objects.all()
    serializer_class = PlantationSerializer
    http_method_names = ['get', 'post', 'patch', 'delete']
    filterset_fields = ["plantation__c_code"]
    filter_backends = [DjangoFilterBackend]
    read_only_fields = ['id']
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        return PlanPart.objects.filter(delete_flag='N')


