from django.db.models import F, Count
from rest_framework import viewsets
from rest_framework.decorators import action

from api.models import OrderMaster, ItemMaster, UserMaster, Plantation
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import serializers
from rest_framework.response import Response
import uuid, json



class PlantationSerializer(serializers.ModelSerializer):

    class Meta:
        model = Plantation
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
        ret = Plantation.objects.values('owner_id', 'c_code')
        group_ret_by_owner = []
        for i in ret:
            if i['owner_id'] not in [x['owner_id'] for x in group_ret_by_owner]:
                group_ret_by_owner.append({'owner_id': i['owner_id'], 'containers': [i['c_code']]})
            else:
                for j in group_ret_by_owner:
                    if j['owner_id'] == i['owner_id']:
                        j['containers'].append(i['c_code'])

        return Response(group_ret_by_owner)


