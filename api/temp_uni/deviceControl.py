from rest_framework import viewsets

from api.models import BomMaster, tempUniControl
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import serializers
from django.db import transaction
from rest_framework.permissions import IsAuthenticated, AllowAny

CONT_UNI = {
    "펌프": 1,
    "교반기": 2,
    "팬1,2": 3,
    "led1": 4,
    "led2": 5,
    "디스펜스 1": 6,
    "디스펜스 2": 7,
    "디스펜스 3": 8,
    "냉난방기": 9,
    "양액기 Dispensor 4": 10,
    "양액기 Dispensor 5": 11,
    "양액기 Dispensor 6": 12,
    "순환 모터": 13,
    "열교환기 A": 14,
    "열교환기 B": 15
}
Except = {
    '양액기 Dispensor 4': 10,
    '양액기 Dispensor 5': 11,
    '양액기 Dispensor 6': 12,
    '순환 모터': 13,
    '열교환기 A': 14,
    '열교환기 B': 15
}

class tempUniCtlSerializer(serializers.ModelSerializer):
    class Meta:
        model = tempUniControl
        fields = '__all__'

    def create(self, validated_data):
        with transaction.atomic():
            ret = tempUniControl.objects.create(**validated_data)
            return ret


class tempUniCtlViewSet(viewsets.ModelViewSet):
        queryset = tempUniControl.objects.all()
        serializer_class = tempUniCtlSerializer
        http_method_names = ['post']
        filter_backends = [DjangoFilterBackend]
        read_only_fields = ['id']
        permission_classes = [AllowAny]

        def get_queryset(self):
            return tempUniControl.objects.filter()

        def create(self, request, *args, **kwargs):
            part_code = BomMaster.objects.get(id=request.data['senid']).part_code
            if part_code in Except:
                return 1
            request.data['key'] = CONT_UNI[part_code]
            request.data['serial'] = part_code
            request.data['control_value'] = 1
            try:
                reserved = request.data['reserved']
                request.data['reserved'] = reserved
                request.data['start_time'] = request.data['start_time'] if reserved == 1 in request.data else None
                request.data['end_time'] = request.data['end_time'] if reserved == 1 in request.data else None
            except:
                pass
            request.data['exec_period'] = request.data['exec_period'] if 'exec_period' in request.data else None
            request.data['rest_period'] = request.data['rest_period'] if 'rest_period' in request.data else None
            request.data['mode'] = request.data['mode'] if 'mode' in request.data else 'M'

            return super().create(request, *args, **kwargs)