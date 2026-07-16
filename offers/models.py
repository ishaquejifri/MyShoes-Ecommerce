from django.db import models
from django.utils import timezone
from category.models import Category
from products.models import Product
import logging
# Create your models here.

logger = logging.getLogger('project_logger')


#base offer model(abstract)
class BaseOffer(models.Model):

    name = models.CharField(max_length=200)
    discount = models.DecimalField(max_digits=5,decimal_places=2,help_text='Discount percentage (0-100)')
    start_date = models.DateField()
    end_date = models.DateField()

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('expired', 'Expired'),
    ]

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    description = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        ordering = ['-created_at']

    @property
    def is_active(self):
        # check the order is currently valid

        today = timezone.now().date()

        return (self.status.lower() == 'active' and self.start_date <= today <= self.end_date)

    def __str__(self):
        ''' string representation shown in django admin
            Example : Summer Sale (30%)'''   
        return f'{self.name} ({self.discount}%)' 


class CategoryOffer(BaseOffer):
    # offer applied to entire category

    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='category_offers')
    class Meta:
        ordering = ['-created_at']

class ProductOffer(BaseOffer):
    # offer applied to specific product

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='product_offers')
    class Meta:
        ordering = ['-created_at']
