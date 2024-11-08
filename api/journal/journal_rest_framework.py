from datetime import datetime
from rest_framework import viewsets
from api.models import Journal , UserMaster, imgJournal, JournalDone, Plantation
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import serializers
from django.db import transaction
from rest_framework.response import Response
from rest_framework.decorators import action



class JournalSerializer(serializers.ModelSerializer):
    related_img = serializers.SerializerMethodField()
    done_journal = serializers.SerializerMethodField()
    class Meta:
        model = Journal
        fields = '__all__'
        extra_kwargs = {
            'delete_flag': {'required': False},
        }
        read_only_fields = ['id']

    
    def get_related_img(self, instance):
        return imgJournal.objects.filter(journal_id=instance.id).values_list('image', flat=True)

    def delete (self, instance):
        instance['delete_flag'] = 'Y'
        return super().update(instance)
    
    def get_done_journal(self, instance):
        if instance.done_flag == 'Y':
            done_journal = JournalDone.objects.filter(journal_id=instance.id).values()
            return done_journal
        return None
    

class JounralViewSet(viewsets.ModelViewSet):

    queryset = Journal.objects.all()
    serializer_class = JournalSerializer
    http_method_names = ['get', 'post', 'patch', 'delete']
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['done_flag', 'plantation__owner_id', "date"]
    read_only_fields = ['id']
    permission_classes = []

    def get_queryset(self):
        ret = Journal.objects.filter(delete_flag='N')
        if self.request.query_params.get('container_id'):
            ret = ret.filter(plantation__bom_id=self.request.query_params.get('container_id'))
        return ret
    
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
    
    def create(self, request, *args, **kwargs):
        request.data['user'] = request.data['user_id']
        request.data['plantation'] = Plantation.objects.get(bom_id=request.data['container_id']).id
        res = super().create(request, *args, **kwargs)
        ImgFiles = request.FILES.getlist('imgFiles')  # getlist 사용으로 다중 파일 처리
        for imgFile in ImgFiles:
            imgJournal.objects.create(journal_id=res.id, img=imgFile)
        return res
    
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        if(instance.done_flag == 'Y'):
            return Response({'message': '작성이 완료된 일지는 수정할 수 없습니다.'})
        return super().update(request, *args, **kwargs)
    
    @action(detail=True, methods=['post', 'patch', 'delete'])
    def done_journal(self, request, *args, **kwargs):
        data = request.data
        instance = self.get_object()
        if request.method == 'POST':
            instance.done_flag = 'Y'
            instance.save()
            print({key: value for key, value in data.items()})
            JournalDone.objects.create(
                **{key: value for key, value in data.items()},
                journal_id=instance.id,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
        # 수정
        elif request.method == 'PATCH': 
            instance.done_journal.update(
                **data,
                updated_at=datetime.now()
            )
        else:
            instance.done_flag = 'N'
            instance.done_journal.delete()
            instance.save()
        return Response({'message': 'success'})
    

    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        with transaction.atomic():
            instance.delete_flag = 'Y' 
            instance.save()
        return Response({'message': 'success'})
    
    @action(detail=False, methods=['get'])
    def get_list(self, request):
        queryset = self.get_queryset()
        return Response(queryset.values())

