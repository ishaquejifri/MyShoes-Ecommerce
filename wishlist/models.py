from django.db import models
from accounts.models import CustomUser
from products.models import Product

# Create your models here.

class Wishlist(models.Model):
    user = models.ForeignKey(CustomUser,on_delete=models.CASCADE)
    product = models.ForeignKey(Product,on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user','product')

    def __str__(self):
        return f'{self.user.email} - {self.product.product_name}'     
     

