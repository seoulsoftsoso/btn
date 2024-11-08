from django.db.models import F, Count
from rest_framework import viewsets
from rest_framework.decorators import action

from api.models import Plantation
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import serializers
from rest_framework.response import Response



class PlantationSerializer(serializers.ModelSerializer):

    class Meta:
        model = Plantation
        fields = '__all__'
        extra_kwargs = {
        }
        read_only_fields = ['id']
        ref_name= 'PlanPartPlantationSerializer'



    def delete(self, instance):
        instance['delete_flag'] = 'Y'
        return super().update(instance)


class PlantationViewSet(viewsets.ModelViewSet):
    queryset = Plantation.objects.all()
    serializer_class = PlantationSerializer
    http_method_names = ['get', 'post', 'patch', 'delete']
    filter_backends = [DjangoFilterBackend]
    read_only_fields = ['id']
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        return Plantation.objects.filter(delete_flag='N')

    @action(detail=False, methods=['GET'])
    def get_container_by_owner(self, request, pk=None):
        ret = Plantation.objects.values('owner_id', 'c_code', 'plant_type', 'test_flag')
        group_ret_by_owner = []
        for i in ret:
            print(i)
            if i['owner_id'] not in [x['owner_id'] for x in group_ret_by_owner]:
                group_ret_by_owner.append({'owner_id': i['owner_id'], 'containers': [{
                            "c_code": i['c_code'],
                            "plant_type": i['plant_type'],
                            "test_flag": i['test_flag'],
                        }]})
            else:
                for j in group_ret_by_owner:
                    if j['owner_id'] == i['owner_id']:
                        j['containers'].append({
                            "c_code": i['c_code'],
                            "plant_type": i['plant_type'],
                            "test_flag": i['test_flag'],
                        })

        return Response(group_ret_by_owner)


