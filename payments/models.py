from django.db import models
from accounts.models import CustomUser
from orders.models import Order

# Create your models here.

class Payment(models.Model):
    PAYMENT_STATUS = (
        ('Pending', 'Pending'),
        ('Success', 'Success'),
        ('Failed', 'Failed'),
        ('Refunded', 'Refunded'),
    )

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE )

    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='payment')

    razorpay_payment_id = models.CharField(max_length=200,blank=True,null=True)

    razorpay_signature = models.TextField(blank=True, null=True)

    amount = models.DecimalField(max_digits=10,decimal_places=2)

    status = models.CharField(max_length=20,choices=PAYMENT_STATUS,default='Pending')

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.order.order_id}'
    
            

