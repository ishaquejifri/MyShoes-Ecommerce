from django.db import models
from accounts.models import CustomUser
from products.models import Product,ProductVariant

# Create your models here.

class Cart(models.Model):
    user = models.OneToOneField(CustomUser,on_delete=models.CASCADE,related_name='cart')
    total = models.DecimalField(max_digits=10,decimal_places=2,default=0.00)
    status = models.CharField(max_length=20,default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart - {self.user.email}"
    
class CartItem(models.Model):
    MAX_QUANTITY_PER_PRODUCT = 5
    cart = models.ForeignKey(Cart,on_delete=models.CASCADE,related_name='items')
    product = models.ForeignKey(Product,on_delete=models.CASCADE)
    variant = models.ForeignKey(ProductVariant,on_delete=models.CASCADE,null=True,blank=True)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10,decimal_places=2) #price at the time of adding
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateField(auto_now=True)

    def subtotal(self):
        if self.product.offer_price:
            return self.quantity * self.product.offer_price
        return self.quantity * self.product.base_price
    
    def __str__(self):
        return f"{self.product.product_name} - {self.quantity}"
