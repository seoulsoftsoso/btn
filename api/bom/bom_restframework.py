import ast
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.decorators import action
from api.models import BomMaster, ItemMaster, OrderProduct, UserMaster, tempUniControl, SenControl, Relay, Plantation
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.db.models import Q
from rest_framework import serializers
import uuid
from pytz import timezone, utc
from datetime import datetime, timedelta
from bson.codec_options import CodecOptions
from functools import reduce
import operator

from django.db.models import Q
import certifi
from pymongo import MongoClient

DB_NAME = 'djangoConnectTest'
GATHER = 'sen_gather'
SENSOR = "sen_status"
SERVER_URL = "mongodb+srv://sj:1234@cluster0.ozlwsy4.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"



ENV_STATUS = {
    "TEMP": "온도센서",
    "HUMI": "습도센서",
    "CO2": "CO2센서",
    "PH": "PH",
    "EC": "EC",
    "LUX": "광센서"
}

class BomMasterSerializer(serializers.ModelSerializer):
    item_price = serializers.FloatField(source='item.standard_price', read_only=True)
    product_info = serializers.CharField(source='item.item_name', read_only=True)
    image = serializers.CharField(source='item.brand', read_only=True)
    product_name = serializers.CharField(source='item.item_name', read_only=True)
    created_by = serializers.CharField(required=False, read_only=True)  # 최종작성일
    updated_by = serializers.CharField(required=False, read_only=True)  # 최종작성자
    delete_flag = serializers.CharField(required=False, read_only=True)  # 삭제여부

    class Meta:
        model = BomMaster
        fields = "__all__"

    def create(self, instance):
        instance['created_by'] = self.get_by_username()
        instance['updated_by'] = self.get_by_username()
        instance['delete_flag'] = 'N'

        return super().create(instance)

    def update(self, instance, validated_data):
        validated_data['updated_by'] = self.get_by_username()
        return super().update(instance, validated_data)

    def delete(self, instance):
        instance['delete_flag'] = 'Y'
        return super().update(instance)


class BomCreateSerializer(serializers.ModelSerializer):
    created_by = serializers.StringRelatedField(read_only=True)
    updated_by = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = BomMaster
        fields = '__all__'

    def get_by_username(self):
        User = UserMaster.objects.get(user_id=self.context['request'].user.id)
        return User.id

    def create(self, instance):
        instance['created_by_id'] = self.get_by_username()

        instance['updated_by_id'] = self.get_by_username()

        return super().create(instance)

    def update(self, instance, validated_data):
        validated_data['updated_by'] = self.get_by_username()

        return super().update(instance, validated_data)


class BomViewSet(viewsets.ModelViewSet):
    queryset = BomMaster.objects.filter(delete_flag='N')
    serializer_class = BomMasterSerializer
    http_method_names = ['get', 'post', 'patch', 'delete']
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['order']
    read_only_fields = ['id']
    permission_classes = [IsAuthenticated]  # Default permission class

    def get_queryset(self):
        qs = BomMaster.objects.filter(delete_flag='N')
        return qs

    def create(self, request, *args, **kwargs):
        rawData = request.data
        item = get_object_or_404(ItemMaster, id=rawData['item_id'])
        order_cnt = int(rawData['order_cnt'])
        parent = rawData.get('parent', '#')
        parent_op_id = None
        level = 0
        if parent and parent != '#':
            parent_bom = get_object_or_404(BomMaster, id=parent)
            parent_op_id = parent_bom.op.id
            level = parent_bom.level + 1
        user = UserMaster.objects.get(user_id=request.user.id)
        boms = []
        for i in range(0, order_cnt):
            bom = BomMaster.objects.create(
                part_code=rawData.get('text', ''),
                item_id=rawData['item_id'],
                order_cnt=1,
                total=item.standard_price,
                tax=item.standard_price * 0.1,
                order_id=rawData['order_id'],
                parent_id=parent,
                level=level,
                delete_flag='N',
                created_by=user,
                updated_by=user,
                op_id=parent_op_id
            )
            boms.append(bom.id)
            if level == 0:
                op = OrderProduct.objects.create(
                    unique_no=str(uuid.uuid4()),
                    product_name=item.item_name,
                    order_id=rawData['order_id'],
                    delivery_date=datetime.now(timezone('Asia/Seoul')),
                    op_cnt=order_cnt,
                    delivery_addr='HCM',
                    request_note='Test',
                    status='1',
                    delete_flag='N',
                    bom=bom,
                    created_by=user,
                    updated_by=user
                )
                bom.op = op
                bom.save()
        return Response({'message': 'success', 'boms': boms}, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['patch'])
    def edit_bom_data(self, request, *args, **kwargs):
        bom_id = kwargs.get('pk')
        bom = get_object_or_404(BomMaster, id=bom_id)
        data = request.data
        order_cnt = int(data['order_cnt'])
        item_totalPrice = bom.item.standard_price * order_cnt
        part_code = data.get('part_code', '')
        bomEditData = {
            'order_cnt': order_cnt,
            'total': item_totalPrice,
            'tax': item_totalPrice * 0.1,
            'part_code': part_code
        }
        bom.__dict__.update(bomEditData)
        bom.save()
        return Response({'message': 'success'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['delete'])
    def delete_bom(self, request, pk=None):
        bom = get_object_or_404(BomMaster, id=pk)
        queue = [bom]
        batch_size = 100
        while queue:
            batch = queue[:batch_size]
            queue = queue[batch_size:]
            with transaction.atomic():
                for current in batch:
                    current.delete_flag = 'Y'
                    current.save()
                    try:
                        order_product = OrderProduct.objects.get(id=current.op_id)
                        order_product.delete_flag = 'Y'
                        order_product.save()
                    except OrderProduct.DoesNotExist:
                        pass
                    children = BomMaster.objects.filter(parent_id=current.id)
                    queue.extend(children)
        return Response({'message': 'success'}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def temp_uni_insert(self, request, prev_time=None, *args, **kwargs):
        data = request.data
        try:
            # 컨테이너 및 센서, 제어 장치 객체 가져오기
            container = BomMaster.objects.get(part_code="uni-container")
            sensor = BomMaster.objects.filter(order__client_id=6, item__item_type='L')
            control = BomMaster.objects.filter(order__client_id=6, item__item_type='C')
        except BomMaster.DoesNotExist:
            return Response({'message': 'Item not found'}, status=status.HTTP_404_NOT_FOUND)

        # 센서 데이터 준비
        pre_sensor_data = []
        for key, value in ENV_STATUS.items():
            try:
                sensor_id = sensor.get(item__item_name=value).id
                pre_sensor_data.append({
                    "c_date": datetime.now(timezone('Asia/Seoul')),
                    "con_id": container.id,
                    "senid": sensor_id,
                    "type": "gta",
                    "value": data.get(key, None)  # 데이터가 없는 경우를 처리
                })
            except BomMaster.DoesNotExist:
                continue

        # 제어 장치 데이터 준비
        pre_control_data = []
        for key, value in CONT_UNI.items():
            try:
                control_id = control.get(part_code=value).id
                pre_control_data.append({
                    "c_date": datetime.now(timezone('Asia/Seoul')),
                    "con_id": container.id,
                    "senid": control_id,
                    "type": "sta",
                    "status": "on" if data['RELAY'][key - 1] == 1 else "off"
                })
            except BomMaster.DoesNotExist:
                continue
            except IndexError:
                continue  # 인덱스 오류 처리
        mongo = MongoClient(SERVER_URL)

        DB_NAME = data['container']
        try:
            db = mongo[DB_NAME]
            collection = db.list_collection_names()
            if GATHER not in collection:
                db.create_collection(GATHER)
            if SENSOR not in collection:
                db.create_collection(SENSOR)
        except Exception as e:
            return Response({'message': 'Database error', 'error': str(e)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        try:
            db = mongo[DB_NAME]
            sen_collection = db[GATHER]
            con_collection = db[SENSOR]
            sen_collection.insert_many(pre_sensor_data)
            con_collection.insert_many(pre_control_data)
        except Exception as e:
            return Response({'message': 'Database error', 'error': str(e)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # 제어 장치 데이터 준비
        sen_control_data = []
        for sen_control in tempUniControl.objects.filter(delete_flag='N'):
            key, value = sen_control.key, sen_control.control_value
            key = int(key)
            data = {
                'key': f'relay {key}',
                'control_value': value
            }
            sen_control_data.append(data)
            sen_control.delete_flag = "Y"
            sen_control.save()
        return Response(sen_control_data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def sen_control(self, request, *args, **kwargs):
        data = request.data
        now_date = datetime.now(timezone('Asia/Seoul'))
        now_time = now_date.strftime("%H%M")
        try:
            # 컨테이너 및 센서, 제어 장치 객체 가져오기
            container = BomMaster.objects.get(part_code=data['container'])
            plantation_id = Plantation.objects.get(bom_id=container.id).id
            sensor = BomMaster.objects.filter(parent__parent_id=container.id, item__item_type='L')
            control = BomMaster.objects.filter(parent__parent_id=container.id, item__item_type='C')
            print(sensor, container.id)
        except BomMaster.DoesNotExist:
            return Response({'message': 'Item not found'}, status=status.HTTP_404_NOT_FOUND)
        # 센서 데이터 준비
        pre_sensor_data = []
        for key, value in ENV_STATUS.items():
            try:
                sen = sensor.filter(item__item_name=value).first().id
                print(sen)
                pre_sensor_data.append({
                    "c_date": datetime.now(timezone('Asia/Seoul')),
                    "con_id": container.id,
                    "senid": sen,
                    "type": "gta",
                    "value": data.get(key, None)  # 데이터가 없는 경우를 처리
                })
            except BomMaster.DoesNotExist:
                continue
            except AttributeError:
                continue
        # 제어 장치 데이터 준비
        pre_control_data = []
        for idx, sen, relay in Relay.objects.filter(container_id=plantation_id).values_list('key', "sen", "id" ):
            pre_control_data.append({
                "c_date": datetime.now(timezone('Asia/Seoul')),
                "con_id": container.id,
                "senid": sen,
                "type": "sta",
                "status": "on" if data['RELAY'][idx - 1] == 1 else "off"
            })
            current_status = SenControl.objects.filter(relay = relay).last()
            if current_status and current_status.mode.startswith("RSV"):
                day = 0
                value = ast.literal_eval(current_status.value)
                end_time = value[1]
                if type(end_time) == int:
                    end_time = str(end_time)
                if(datetime.strptime(now_time, "%H%M") > datetime.strptime(end_time, "%H%M")):
                    day = 1
                if datetime.strptime(now_time, "%H%M") >= datetime.strptime(end_time, "%H%M") + timedelta(days=day):
                    SenControl.objects.create(
                        part_code=current_status.part_code,
                        mode="CTR_VAL",
                        value=0,
                        relay_id=relay
                    )
        # MongoDB에 데이터 삽입
        try :
            mongo = MongoClient(SERVER_URL, tlsCAFile=certifi.where())
            if mongo[DB_NAME].list_collection_names() == []:
                mongo[DB_NAME].create_collection(GATHER)
                mongo[DB_NAME].create_collection(SENSOR)
        except Exception as e:
            return Response({'message': 'Database error', 'error': str(e)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        try:
            mongo = MongoClient(SERVER_URL, tlsCAFile=certifi.where())
            db = mongo[DB_NAME]
            if len(pre_sensor_data) > 0:
                sen_collection = db[GATHER]
                sen_collection.insert_many(pre_sensor_data)
            if len(pre_control_data) > 0:
                con_collection = db[SENSOR]
                con_collection.insert_many(pre_control_data)
        except Exception as e:
            return Response({'message': 'Database error', 'error': str(e)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # # 제어 장치 데이터 준비
        res = []
        req_time = data['TIME']
        time_set = False
        if req_time != now_time:
            time_set = True

        for sen_control in SenControl.objects.filter(delete_flag='N'):
            mode, value, part_code, relay = sen_control.mode, sen_control.value, sen_control.part_code, sen_control.relay
            value = ast.literal_eval(value) 
            if mode == "SV":
                sv_relay = control.filter(
                    item__sensor_type=part_code,
                    item__sv_reverse=None
                ).values_list('id', flat=True)
                sv_relay_reverse = control.filter(
                    item__sensor_type=part_code,
                    item__sv_reverse=1
                ).values_list('id', flat=True)
                keys = Relay.objects.filter(
                    container_id=plantation_id, sen_id__in=sv_relay
                ).values_list('key', flat=True)
                keys_reverse = Relay.objects.filter(container_id=plantation_id, sen_id__in=sv_relay_reverse).values_list('key', flat=True)
                if keys:
                    res.append({
                        'key': list(keys),
                        "mode": mode,
                        "value": reduce(operator.concat, value) if type(value) == "list" else value,
                        'reverse': False
                    })
                if keys_reverse:
                    res.append({
                        'key': list(keys_reverse),
                        "mode": mode,
                        "value": reduce(operator.concat, value) if type(value) == "list" else value,
                        "reverse": True
                    })
                sen_control.delete_flag = 'Y'
                sen_control.save()
            elif part_code == "ALL":
                if mode == "CHK":
                    for i in Relay.objects.filter(container_id=plantation_id):
                        curr_status = SenControl.objects.filter(
                            Q(part_code=i.key) | Q(part_code="ALL")
                        ).exclude(id=sen_control.id).last()
                        if curr_status:
                            curr_mode = curr_status.mode
                            curr_value = curr_status.value
                            res.append({
                                'key': i.key,
                                "chk": 1,
                                "mode": curr_mode,
                                "value":  reduce(operator.concat, value) if type(value) == "list" else value,
                            })
                        else:
                            res.append({
                                'key': i.key,
                                "chk": 0,
                            })
                    sen_control.delete()
                    continue
                else:
                    for i in Relay.objects.filter(container_id=plantation_id):
                        res.append({
                            'key': i.key,
                            "mode": mode,
                            "value":  reduce(operator.concat, value) if type(value) == "list" else value,
                        })
                sen_control.delete_flag = 'Y'
                sen_control.save()
                continue
            elif mode == "CHK":
                curr_status = SenControl.objects.filter(
                    Q(part_code=part_code) | Q(part_code="ALL")
                ).exclude(id=sen_control.id).last()
                if curr_status:
                    curr_mode = curr_status.mode
                    curr_value = curr_status.value
                    res.append({
                        'key': relay.key,
                        "chk": 1,
                        "mode": curr_mode,
                        "value":  reduce(operator.concat, value) if type(value) == "list" else value,
                    })
                else:
                    res.append({
                        'key': relay.key,
                        "chk": 0,
                    })
                sen_control.delete()
            else:
                res.append({
                    'key': relay.key,
                    "mode": mode,
                    "value":  reduce(operator.concat, value) if type(value) == "list" else value,
                })
                sen_control.delete_flag = 'Y'
                sen_control.save()
        if time_set and res:
            res[0]['time'] = now_time
        return Response(res)
