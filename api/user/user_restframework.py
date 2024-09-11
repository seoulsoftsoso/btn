from rest_framework import viewsets

from api.models import UserMaster, EnterpriseMaster
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import serializers
from django.db import transaction
from django.contrib.auth.models import User
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny



def format_data(data):
    return {
        'user':  {
            'user_code': data['user_code'] if 'user_code' in data else '',
            'user_name': data['user_name'],
            'tel': data['tel'],
            'address': data['address'],
            'signature': data['signature'] if 'signature' in data else '',
        },
        'ent': {
            'licensee_no': data['licensee_no'],
            'owner_name': data['owner_name'] if 'owner_name' in data else '',
            'charge_name': data['charge_name'] if 'charge_name' in data else '',
            'company_name': data['company_name'] if 'company_name' in data else '',
            'charge_pos': data['charge_pos'] if 'charge_pos' in data else '',
            'charge_tel': data['charge_tel'] if 'charge_tel' in data else '',
        },
        'password': data['password'],
        'confirm_password': data['confirm_password']
    }


class EntSerializer(serializers.ModelSerializer):

    class Meta:
        model = EnterpriseMaster
        fields = '__all__'
        extra_kwargs = {
            'delete_flag': {'required': False},
            'created_by': {'required': False},
            'updated_by': {'required': False}
        }
        read_only_fields = ['id']

    def get_by_username(self):
        return UserMaster.objects.get(user=self.context['request'].user)

    def create(self, instance):
        instance['created_by'] = self.get_by_username()
        instance['updated_by'] = self.get_by_username()
        instance['delete_flag'] = 'N'

        return super().create(instance)

    def update(self, instance, validated_data):
        validated_data['updated_by'] = self.get_by_username()

        return super().update(instance, validated_data)

    def delete (self, instance):
        instance['delete_flag'] = 'Y'
        return super().update(instance)


class EntViewSet(viewsets.ModelViewSet):
        queryset = EnterpriseMaster.objects.all()
        serializer_class = EntSerializer
        http_method_names = ['get', 'post', 'patch', 'delete']
        filter_backends = [DjangoFilterBackend]
        read_only_fields = ['id']
        permission_classes = [IsAuthenticated]

        def get_queryset(self):
            return EnterpriseMaster.objects.filter(delete_flag='N')

        def create(self, request, *args, **kwargs):
            rawData = format_data(request.data)['ent']
            with transaction.atomic():
                ent = EnterpriseMaster.objects.create(
                    **rawData
                )
            return ent
class UserSerializer(serializers.ModelSerializer):
    ent = EntSerializer()

    class Meta:
        model = UserMaster
        fields = '__all__'
        extra_kwargs = {
            'delete_flag': {'required': False},
            'created_by': {'required': False},
            'updated_by': {'required': False},
            'signature': {'required': False},
            'user': {'required': False},
        }
        read_only_fields = ['id']

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret['email'] = instance.user.email
        return ret

class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserMaster
        fields = ['id', 'user_name', 'tel', 'address', 'signature']
        extra_kwargs = {
            'delete_flag': {'required': False},
            'created_by': {'required': False},
            'updated_by': {'required': False}
        }
        read_only_fields = ['id']

    def get_by_username(self):
        return UserMaster.objects.get(user=self.context['request'].user)

class UserViewSet(viewsets.ModelViewSet):

    queryset = UserMaster.objects.all()
    serializer_class = UserSerializer
    http_method_names = ['get', 'post', 'patch', 'delete']
    filter_backends = [DjangoFilterBackend]
    read_only_fields = ['id']
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserMaster.objects.filter(delete_flag='N')

    def get_permissions(self):
        if self.action == 'create':
            self.permission_classes = [AllowAny]
        else:
            self.permission_classes = [IsAuthenticated]
        return super().get_permissions()


    def create(self, request, *args, **kwargs):
        rawData = request.data
        formattedData = format_data(rawData)
        if rawData['password'] != rawData['confirm_password']:
            return Response({'error': '비밀번호가 일치하지 않습니다.'}, status=400)
        user = {
            'username' : rawData['user_name'], # 'username' : 'user_name' -> 'username' : 'user_name
            'email' :rawData['email'],
            'password' :rawData['password'],
        }
        auth_user = User.objects.create_user(
            **user
        )
        Ent = EnterpriseMaster.objects.create(
            **formattedData['ent'],
            delete_flag='N'
        )
        user = UserMaster.objects.create(
            user=auth_user,
            **formattedData['user'],
            delete_flag= 'N',
            ent=Ent
        )
        return Response({'status': 'success'})

    def update(self, request, *args, **kwargs):
        rawData = format_data(request.data)
        with transaction.atomic():
            user = UserMaster.objects.get(id=kwargs['pk'])
            auth_user = user.user
            user.__dict__.update(rawData['user'])
            ent = user.ent
            ent.__dict__.update(rawData['ent'])
            ent.save()
            if rawData['confirm_password'] == rawData['password'] and len(rawData['password']) >=6 :
                auth_user.set_password(rawData['password'])
                auth_user.save()
            user.save()
        return Response({'status': 'success'})

    def delete(self, request, *args, **kwargs):
        user = UserMaster.objects.get(id=kwargs['pk'])
        user.delete_flag = 'Y'
        user.ent.delete_flag = 'Y'
        user.ent.save()
        user.save()
        return Response({'status': 'success'})
