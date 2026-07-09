from django.db import models
from accounts.models import CustomUser,Address
from products.models import Product,ProductVariant
from decimal import Decimal
# Create your models here.

class Order(models.Model):
    order_id = models.CharField(max_length=10,unique=True,editable=False)
    user = models.ForeignKey(CustomUser,on_delete=models.PROTECT,related_name='orders')
    shipping_address = models.ForeignKey(Address,on_delete=models.SET_NULL,null=True,related_name='orders')
    
    full_name = models.CharField(max_length=100)
    mobile = models.CharField(max_length=15)
    street_address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)

    STATUS_CHOICES = [
             
        ("pending","Pending"),
        ("confirmed","Confirmed"),
        ("processing","Processing"),
        ("shipped","Shipped"),
        ("out_for_delivery","Out for Delivery"),
        ("delivered","Delivered"),
        ("cancelled","Cancelled"),
        ("return_requested","Return Requested"),
        ("returned","Returned"),
        ("return_rejected","Return Rejected"),
    ]

    PAYMENT_METHOD_CHOICES = [
        ("cod","Cash on Delivery"),
        ("online","Online Payment"),
        ("wallet","Wallet"),
    ]

    PAYMENT_STATUS = [
        ('Paid', 'Paid'),
        ('Pending', 'Pending'),
        ('Failed', 'Failed'),
        ('Cancelled', 'Cancelled'),
        ('Refunded', 'Refunded'),
    ]

    status = models.CharField(max_length=200,choices=STATUS_CHOICES,default='pending')

    payment_method = models.CharField(max_length=20,choices=PAYMENT_METHOD_CHOICES,default='cod')
    payment_status = models.CharField(max_length=20,choices=PAYMENT_STATUS,default='pending')

    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    sub_total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    shipping_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    coupon_discount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))

    created_at = models.DateTimeField(auto_now_add=True)
    cancellation_reason = models.TextField(blank=True,null=True)
    return_reason = models.TextField(blank=True,null=True) 

    def __str__(self):
        return f"Order #{self.order_id}"
    
    def update_total(self):
        active_items = self.items.exclude(item_status__in=['cancelled', 'returned', 'Cancelled', 'Returned'])

        subtotal = sum(
        item.price * item.quantity
        for item in active_items
    )

        self.sub_total = subtotal

        shipping = self.shipping_charge

        if not active_items.exists():
            shipping = 0

        self.total_amount = (
        subtotal +
        shipping -
        self.discount_amount
    )

        self.save()

class OrderItem(models.Model):
    order = models.ForeignKey(Order,on_delete=models.CASCADE,related_name='items')
    product = models.ForeignKey(Product,on_delete=models.CASCADE)
    variant = models.ForeignKey(ProductVariant,on_delete=models.CASCADE)

    product_name = models.CharField(max_length=200)
    variant_size = models.CharField(max_length=20)
    variant_color = models.CharField(max_length=20)

    price = models.DecimalField(max_digits=10,decimal_places=2)
    original_price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_amount = models.DecimalField(max_digits=10,decimal_places=2,default=0.00)
    quantity = models.PositiveIntegerField()
    

    STATUS_CHOICES = [
        ('placed','Placed'),
        ('pending','Pending'),
        ('confirmed','Confirmed'),
        ('processing','Processing'),
        ('shipped','Shipped'),
        ('out_for_delivery','Out for Delivery'),
        ('delivered','Delivered'),
        ('cancelled','Cancelled'),
        ('return_requested','Return Requested'),
        ('returned','Returned'),
    ]

    item_status = models.CharField(max_length=20,choices=STATUS_CHOICES,default='placed')

    def __str__(self):
        return f"{self.product.product_name} - {self.quantity}"
    
class OrderStatusHistory(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='history')
    status = models.CharField(max_length=50)
    timestamp = models.DateTimeField(auto_now_add=True)    
    note = models.TextField(blank=True,null=True)
