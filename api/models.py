from django.db import models
from django.contrib.auth.models import User

class UserMaster(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    user_code = models.CharField(max_length=255)
    user_name = models.CharField(max_length=255)
    address = models.CharField(max_length=255, null=True)
    tel = models.CharField(max_length=255, null=True)
    fax = models.CharField(max_length=255, null=True)
    signature = models.ImageField(upload_to='user_signatures/', null=True)
    ent = models.ForeignKey('EnterpriseMaster', on_delete=models.CASCADE, null=True)
    delete_flag = models.CharField(max_length=1, choices=(('Y', 'Yes'), ('N', 'No')))
    is_master = models.CharField(max_length=1, choices=(('Y', 'Yes'), ('N', 'No')))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'userMaster'


class EnterpriseMaster(models.Model):
    company_name = models.CharField(max_length=255)
    licensee_no = models.CharField(max_length=255, null=True)
    owner_name = models.CharField(max_length=255)
    bus_con = models.CharField(max_length=255, null=True)
    bus_event = models.CharField(max_length=255, null=True)
    postal_code = models.CharField(max_length=255, null=True)
    addr = models.CharField(max_length=255, null=True)
    office_tel = models.CharField(max_length=255, null=True)
    office_fax = models.CharField(max_length=255, null=True)
    office_email = models.EmailField(null=True)
    charge_name = models.CharField(max_length=255, null=True)
    charge_tel = models.CharField(max_length=255, null=True)
    charge_pos = models.CharField(max_length=255, null=True)
    etc = models.TextField(null=True)
    cus_type = models.CharField(max_length=255, null=True)
    delete_flag = models.CharField(max_length=1, choices=(('Y', 'Yes'), ('N', 'No')))
    class Meta:
        db_table = 'enterpriseMaster'


class ItemMaster(models.Model):
    item_code = models.CharField(max_length=255, unique=True)
    item_name = models.CharField(max_length=255)
    item_type = models.CharField(max_length=255)  # L = sensor / C = controller
    sensor_type = models.CharField(max_length=3, choices=( ('HUM', 'HUM'), ('TEM', 'TEM'), ("CO2", "CO2"),
                                                           ("PH", "PH"), ("EC", "EC"), ("LUX", "LUX")
                                                        ), null=True)
    sv_reverse = models.BooleanField(default=False)
    specification = models.TextField(blank=True, null=True)
    model = models.TextField(blank=True, null=True)
    brand = models.CharField(max_length=255, blank=True, null=True)
    level = models.CharField(max_length=255)  # root = container / 1 = controller / 2 = part(item)
    standard_price = models.IntegerField(blank=True, default=999)
    delete_flag = models.CharField(max_length=1, choices=(('Y', 'Yes'), ('N', 'No')))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(UserMaster, related_name='item_created_by', on_delete=models.CASCADE)
    updated_by = models.ForeignKey(UserMaster, related_name='item_updated_by', on_delete=models.CASCADE)

    class Meta:
        db_table = 'itemMaster'


class BasicBom(models.Model):
    bom_code = models.CharField(max_length=255)
    level = models.IntegerField()
    item = models.ForeignKey('ItemMaster', on_delete=models.CASCADE)
    parent = models.ForeignKey('BasicBom', related_name='parent_bom', on_delete=models.CASCADE)
    delete_flag = models.CharField(max_length=1, choices=(('Y', 'Yes'), ('N', 'No')))

    class Meta:
        db_table = 'basicBom'


class BomMaster(models.Model):
    level = models.IntegerField()  # root = 0
    part_code = models.CharField(max_length=255)
    order_cnt = models.IntegerField()
    order = models.ForeignKey('OrderMaster', on_delete=models.SET_NULL, null=True)
    item = models.ForeignKey('ItemMaster', on_delete=models.SET_NULL, null=True)
    parent = models.ForeignKey('BomMaster', related_name='parent_bom', on_delete=models.SET_NULL, null=True,
                               default=None)
    total = models.IntegerField()
    tax = models.IntegerField()
    op = models.ForeignKey('OrderProduct', on_delete=models.SET_NULL, null=True)
    delete_flag = models.CharField(max_length=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(UserMaster, related_name='bom_created_by', on_delete=models.CASCADE)
    updated_by = models.ForeignKey(UserMaster, related_name='bom_updated_by', on_delete=models.CASCADE)

    class Meta:
        db_table = 'bomMaster'


class OrderMaster(models.Model):
    so_no = models.CharField(max_length=255)
    client = models.ForeignKey(UserMaster, on_delete=models.SET_NULL, null=True, related_name='client')
    order_date = models.DateField()
    order_cnt = models.IntegerField()
    order_price = models.IntegerField()
    order_total = models.IntegerField()
    order_tax = models.IntegerField()
    order_sales_by = models.ForeignKey(UserMaster, on_delete=models.SET_NULL, null=True, related_name='sales_by')
    order_place = models.CharField(max_length=255)
    comment = models.TextField()
    delete_flag = models.CharField(max_length=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(UserMaster, related_name='order_created_by', on_delete=models.SET_NULL, null=True)
    updated_by = models.ForeignKey(UserMaster, related_name='order_updated_by', on_delete=models.SET_NULL, null=True)

    class Meta:
        db_table = 'orderMaster'


class OrderProduct(models.Model):
    unique_no = models.CharField(max_length=255)
    product_name = models.CharField(max_length=255)
    order = models.ForeignKey('OrderMaster', on_delete=models.SET_NULL, null=True)
    delivery_date = models.DateTimeField(null=True)
    op_cnt = models.IntegerField(null=True)
    crops = models.CharField(max_length=255, null=True)
    delivery_addr = models.CharField(max_length=255, null=True)
    bom = models.ForeignKey('BomMaster', on_delete=models.SET_NULL, null=True)
    request_note = models.TextField(null=True)
    status = models.CharField(max_length=255, null=True)
    delete_flag = models.CharField(max_length=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(UserMaster, related_name='order_product_created_by', on_delete=models.CASCADE)
    updated_by = models.ForeignKey(UserMaster, related_name='order_product_updated_by', on_delete=models.CASCADE)

    class Meta:
        db_table = 'orderProduct'


class PlanPart(models.Model):
    p_name = models.CharField(max_length=100)
    part = models.ForeignKey(BomMaster, on_delete=models.SET_NULL, null=True)
    plantation = models.ForeignKey('Plantation', on_delete=models.SET_NULL, null=True)
    delete_flag = models.CharField(max_length=1, default='N')
    status = models.CharField(max_length=10, null=True)
    message = models.CharField(max_length=255, null=True)
    type= models.CharField(max_length=10, null=True)
    reg_flag = models.CharField(max_length=1, default='N')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(UserMaster, related_name='created_planpart', on_delete=models.CASCADE)
    updated_by = models.ForeignKey(UserMaster, related_name='updated_planpart', on_delete=models.CASCADE)

    class Meta:
        db_table = 'planPart'


class PlanType(models.Model): 
    name= models.CharField(max_length=100)

    class Meta:
        db_table = 'planType'

class Plantation(models.Model):
    c_code = models.CharField(max_length=50, unique=True)
    c_name = models.CharField(max_length=100)
    owner = models.ForeignKey(UserMaster, on_delete=models.CASCADE)
    bom = models.ForeignKey(BomMaster, on_delete=models.SET_NULL, null=True)
    delete_flag = models.CharField(max_length=1, default='N')
    plant_type = models.ForeignKey('PlanType', on_delete=models.SET_NULL, null=True)
    reg_flag = models.CharField(max_length=1, default='N')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(UserMaster, related_name='created_plantations', on_delete=models.CASCADE)
    updated_by = models.ForeignKey(UserMaster, related_name='updated_plantations', on_delete=models.CASCADE)
    test_flag = models.CharField(max_length=1, default='N')

    class Meta:
        db_table = 'plantation'

class tempUniControl(models.Model):
    key = models.CharField(max_length=255)
    serial = models.CharField(max_length=255, null=True)
    control_value = models.BooleanField(default=False, null=True)
    reserved = models.BooleanField(default=False, null=True)
    set_value = models.FloatField(null=True)
    start_time = models.TimeField(null=True)
    end_time = models.TimeField(null=True)
    delete_flag = models.CharField(max_length=1, default='N')
    exec_period = models.IntegerField(null=True)
    rest_period = models.IntegerField(null=True)
    mode = models.CharField(choices=(("A", "Auto"), ("M", "Manual")), max_length=1)

    class Meta:
        db_table = "tempUniControl"

class Manual(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    delete_flag = models.CharField(max_length=1, default='N')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(UserMaster, related_name='created_manuals', on_delete=models.CASCADE)
    updated_by = models.ForeignKey(UserMaster, related_name='updated_manuals', on_delete=models.CASCADE)
    plant_type = models.ForeignKey('PlanType', on_delete=models.CASCADE)

    class Meta:
        db_table = 'manual'

class script (models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    d_day = models.IntegerField()
    image = models.ImageField(upload_to='manual_images/', null=True)
    manual = models.ForeignKey('Manual', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(UserMaster, related_name='created_scripts', on_delete=models.CASCADE)
    updated_by = models.ForeignKey(UserMaster, related_name='updated_scripts', on_delete=models.CASCADE)

    class Meta:
        db_table = 'script'

class EntManual(models.Model):
    title = models.CharField(max_length=255)
    description = models.CharField(max_length=255)
    date = models.DateField()
    manual = models.ForeignKey('Manual', on_delete=models.CASCADE)
    plantation = models.ForeignKey('Plantation', on_delete=models.CASCADE)
    done_flag = models.CharField(max_length=1, default='N')
    delete_flag = models.CharField(max_length=1, default='N')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(UserMaster, related_name='created_ent_manuals', on_delete=models.CASCADE)
    updated_by = models.ForeignKey(UserMaster, related_name='updated_ent_manuals', on_delete=models.CASCADE)

    class Meta:
        db_table = 'entManual'

class EntScript(models.Model):
    title = models.CharField(max_length=255)
    description = models.CharField(max_length=255)
    date = models.DateField()
    entManual = models.ForeignKey('EntManual', on_delete=models.CASCADE)
    script = models.ForeignKey('script', on_delete=models.CASCADE)
    done_flag = models.CharField(max_length=1, default='N')
    delete_flag = models.CharField(max_length=1, default='N')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(UserMaster, related_name='created_ent_scripts', on_delete=models.CASCADE)
    updated_by = models.ForeignKey(UserMaster, related_name='updated_ent_scripts', on_delete=models.CASCADE)

    class Meta:
        db_table = 'entScript'

class Journal(models.Model):
    amount = models.IntegerField()
    unit = models.CharField(max_length=255)
    temp = models.IntegerField()
    humi = models.IntegerField()
    # title =('입고', '배지관리', '솎아내기', '수확')
    delete_flag = models.CharField(max_length=1, default='N')
    plantation = models.ForeignKey('Plantation', on_delete=models.CASCADE)
    done_flag = models.CharField(max_length=1, default='N')
    title = models.CharField(max_length=255)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(UserMaster, related_name='created_journals', on_delete=models.CASCADE)
    updated_by = models.ForeignKey(UserMaster, related_name='updated_journals', on_delete=models.CASCADE)
    user = models.ForeignKey(UserMaster, on_delete=models.CASCADE)

    class Meta:
        db_table = 'journal'

class imgJournal(models.Model):
    image = models.ImageField(upload_to='journal_images/', null=True)
    journal = models.ForeignKey('Journal', on_delete=models.CASCADE)

    class Meta:
        db_table = 'imgJournal'

class JournalDone(models.Model):
    grade = models.CharField(max_length=1, choices=(('A', 'A등급'), ('B', 'B등급'), ('X', '가치없음')))
    amount = models.FloatField()
    unit = models.CharField(max_length=25, choices=(('kg', '킬로그램'), ('g', '그램'), ('ea', '개'), ('box', '박스')))
    photo = models.ImageField(upload_to='journal_done_images/', null=True)
    journal = models.ForeignKey('Journal', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(UserMaster, related_name='created_journal_done', on_delete=models.CASCADE)
    updated_by = models.ForeignKey(UserMaster, related_name='updated_journal_done', on_delete=models.CASCADE)

    class Meta:
        db_table = 'journalDone'

class SenControl(models.Model):
    part_code = models.CharField(max_length=255)
    mode = models.CharField(max_length=20)
    value = models.CharField(max_length=255)
    relay = models.ForeignKey('Relay', on_delete=models.SET_NULL, null=True)
    delete_flag = models.CharField(max_length=1, default='N')

    class Meta:
        db_table = "senControl"

class Relay(models.Model):
    key = models.IntegerField()
    name = models.CharField(max_length=20)
    sen = models.ForeignKey('BomMaster', on_delete=models.CASCADE)
    container = models.ForeignKey('Plantation', on_delete=models.CASCADE)
    
    class Meta:
        db_table = "relay"    