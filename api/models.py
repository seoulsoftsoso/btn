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
    customer_name = models.CharField(max_length=255)
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
    item_type = models.CharField(max_length=255)
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
    delete_flag = models.CharField(max_length=1, default='N')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(UserMaster, related_name='created_planpart', on_delete=models.CASCADE)
    updated_by = models.ForeignKey(UserMaster, related_name='updated_planpart', on_delete=models.CASCADE)

    class Meta:
        db_table = 'planPart'


class Plantation(models.Model):
    c_code = models.CharField(max_length=50, unique=True)
    c_name = models.CharField(max_length=100)
    owner = models.CharField(max_length=100)
    bom = models.ForeignKey(BomMaster, on_delete=models.SET_NULL, null=True)
    delete_flag = models.CharField(max_length=1, default='N')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(UserMaster, related_name='created_plantations', on_delete=models.CASCADE)
    updated_by = models.ForeignKey(UserMaster, related_name='updated_plantations', on_delete=models.CASCADE)

    class Meta:
        db_table = 'plantation'
