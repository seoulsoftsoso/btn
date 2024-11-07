from django.db.models import F, Count
from rest_framework import viewsets, status
from rest_framework.decorators import action

from api.models import  PlanPart, PlanType
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import serializers
from rest_framework.response import Response



class PlantationSerializer(serializers.ModelSerializer):

    class Meta:
        model = PlanPart
        fields = '__all__'
        extra_kwargs = {

        }
        read_only_fields = ['id']

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

    @action(detail=False, methods=['GET'])
    def get_plant_type(self, request, pk=None):
        ret = PlanType.objects.all().values('id', 'name')
        return Response(ret)
