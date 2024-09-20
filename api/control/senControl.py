from rest_framework import viewsets

from api.models import BomMaster, SenControl
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import serializers
from django.db import transaction
from rest_framework.permissions import AllowAny


class senControlSerializer(serializers.ModelSerializer):
    class Meta:
        model = SenControl
        fields = '__all__'

    def create(self, validated_data):
        with transaction.atomic():
            ret = SenControl.objects.create(**validated_data)
            return ret


class senControlViewSet(viewsets.ModelViewSet):
    queryset = SenControl.objects.all()
    serializer_class = senControlSerializer
    http_method_names = ['post']
    filter_backends = [DjangoFilterBackend]
    read_only_fields = ['id']
    permission_classes = [AllowAny]

    def get_queryset(self):
        return SenControl.objects.filter()

    def create(self, request, *args, **kwargs):
        if request.data['senid'] != "ALL":
            part_code = BomMaster.objects.get(id=request.data['senid']).part_code
        else: 
            part_code = "ALL"
        request.data['part_code'] = part_code

        return super().create(request, *args, **kwargs)