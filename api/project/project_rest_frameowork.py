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

    def get_by_user_id(self):
        return UserMaster.objects.get(user=self.context['request'].user)
    
    def create(self, instance):
        instance['created_by'] = self.get_by_user_id()
        instance['updated_by'] = self.get_by_user_id()
        instance['delete_flag'] = 'N'

        return super().create(instance)

    def update(self, instance, validated_data):
        validated_data['updated_by'] = self.get_by_user_id()

        return super().update(instance, validated_data)

    def delete (self, instance):
        instance['delete_flag'] = 'Y'
        return super().update(instance)
    

class ProjectViewSet(viewsets.ModelViewSet):

    queryset = EntScript.objects.all()
    serializer_class = ProjectSerializer
    http_method_names = ['get', 'post', 'patch', 'delete']
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['date', 'done_flag']
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
        if self.request.query_params.get('current_date'):
            ret = ret.filter(date=self.request.query_params.get('current_date'))
        if self.request.query_params.get('bom_id'):
            ret = ret.filter(plantation__bom_id=self.request.query_params.get('bom_id'))
        return ret    
    
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
    
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        with transaction.atomic():
            instance.update(
                date=request.data['date'],
                done_flag=request.data['done_flag'],
                updated_by=UserMaster.objects.get(user=request.user),
                updated_at=datetime.now()
            )

    @action(detail=False, methods=['post'])
    def create_project(self, request, *args, **kwargs):
        # params: user_id, bom_id, date
        try:
            user_instance = UserMaster.objects.get(user_id=request.data['user_id'])
        except UserMaster.DoesNotExist:
            return Response({'message': '유저가 존재하지 않습니다.'}, status=404)

        try:
            plant = Plantation.objects.get(bom_id=request.data['bom_id'])
            plant_type = plant.plant_type
            manual_id = Manual.objects.get(plant_type=plant_type)
        except BomMaster.DoesNotExist:
            return Response({'message': '컨테이너 아이디가 잘못되었습니다.'}, status=404)
        scripts_by_plant = script.objects.filter(manual=manual_id)
        if not scripts_by_plant.exists():
            return Response({'message': '해당 식물 유형에 대한 스크립트가 없습니다.'}, status=404)

        current_date = datetime.now()
        try:
            curr_date = datetime.strptime(request.data['date'], '%Y-%m-%d')
        except ValueError:
            return Response({'message': '날짜 형식이 잘못되었습니다. 올바른 형식: YYYY-MM-DD'}, status=400)

        ent_scripts_to_create = []

        for obj in scripts_by_plant:
            day_after = curr_date + timedelta(days=obj.d_day)
            ent_scripts_to_create.append(
                EntScript(
                    date=day_after,
                    title = obj.title,
                    description = obj.description,
                    plantation_id = plant.id,
                    created_by=user_instance,
                    updated_by=user_instance,
                    created_at=current_date,
                    updated_at=current_date,
                    delete_flag='N',
                    script=obj,
                    manual=obj.manual
                )
            )

        try:
            EntScript.objects.bulk_create(ent_scripts_to_create)
        except Exception as e:
            return Response({'message': f'추가 중 오류 발생: {str(e)}'}, status=500)

        return Response({'message': 'success'})
        
    @action(detail=True, methods=['get'])
    def exist_project(self, request, *args, **kwargs):
        instance = self.get_object()
        exist = EntScript.objects.filter(date=instance.date, plantation=instance.plantation, Plantation_ent= instance.Plantation_ent).exists()
        return Response({'exist': exist})
    
    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        with transaction.atomic():
            instance.delete_flag = 'Y' 
            instance.save()
        return Response({'message': 'success'})
