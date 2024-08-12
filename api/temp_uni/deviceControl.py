from rest_framework import viewsets

from api.models import BomMaster, tempUniControl
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import serializers
from django.db import transaction
from django.contrib.auth.models import User
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny

CONT_UNI = {
    "FAN 1": 1,
    "FAN 2": 2,
    "LED Dimming 1": 3,
    "LED Dimming 2": 4,
    "LED Dimming 3": 5,
    "LED Dimming 4": 6,
    "양액기 Dispensor 1": 7,
    "양액기 Dispensor 2": 8,
    "양액기 Dispensor 3": 9,
    "양액기 Dispensor 4": 10,
    "양액기 Dispensor 5": 11,
    "양액기 Dispensor 6": 12,
    "순환 모터": 13,
    "열교환기 A": 14,
    "열교환기 B": 15
}

class tempUniCtlSerializer(serializers.ModelSerializer):
    class Meta:
        model = tempUniControl
        fields = '__all__'

    def create(self, validated_data):
        with transaction.atomic():
            tempUniControl = tempUniControl.objects.create(**validated_data)
            return tempUniControl

    def update(self, instance, validated_data):
        with transaction.atomic():
            tempUniControl = tempUniControl.objects.filter(id=instance.id).update(**validated_data)
            return tempUniControl

class tempUniCtlViewSet(viewsets.ModelViewSet):
        queryset = tempUniControl.objects.all()
        serializer_class = tempUniCtlSerializer
        http_method_names = ['post']
        filter_backends = [DjangoFilterBackend]
        read_only_fields = ['id']
        permission_classes = []

        def get_queryset(self):
            return tempUniControl.objects.filter(delete_flag='N')

        def create(self, request, *args, **kwargs):
            request.data._mutable = True
            request.data['key'] = CONT_UNI[BomMaster.objects.get(id=request.data['senid']).part_code]
            return super().create(request, *args, **kwargs)