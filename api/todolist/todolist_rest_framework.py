from rest_framework import viewsets
from api.models import TodoList, Plantation
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import serializers
from django.db import transaction
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny


class TodoListSerializer(serializers.ModelSerializer):
    delete_flag = serializers.CharField(required=False, read_only=True)  # 삭제여부
    class Meta:
        model = TodoList
        fields = '__all__'
        extra_kwargs = {
            'delete_flag': {'required': False},
        }
        read_only_fields = ['id']

    def delete (self, instance) -> TodoList:
        instance['delete_flag'] = 'Y'
        return super().update(instance)


class TodoListViewSet(viewsets.ModelViewSet):

    queryset = TodoList.objects.all()
    serializer_class = TodoListSerializer
    http_method_names = ['get', 'post', 'patch', 'delete']
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['done_flag', 'date']
    ordering_fields = ['date']
    read_only_fields = ['id']
    permission_classes = [AllowAny]

    def get_queryset(self) -> TodoList:
        ret = TodoList.objects.all()
        
        if self.request.query_params.get('container_id'):
            ret = ret.filter(container__bom_id=self.request.query_params.get('container_id'))
        return ret

    def create(self, request, *args, **kwargs) -> Response:
        request.data['container'] = Plantation.objects.get(bom_id=request.data['container_id']).id
        return super().create(request, *args, **kwargs)
    
    def delete(self, request, *args, **kwargs) -> Response:
        instance = self.get_object()
        with transaction.atomic():
            isinstance.delete_flag = 'Y'
            instance.save()
        return Response({'message': 'success'})
    
    @action(detail=True, methods=['patch'])
    def done(self, request, pk=None) -> Response:
        instance = self.get_object()
        instance.done_flag = True
        instance.save()
        return Response({'message': 'success'})

