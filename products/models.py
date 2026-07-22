from django.db import models
from category.models import Category
from django.db.models import Avg,Count
from PIL import Image
from decimal import Decimal
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
import uuid

# Create your models here.

class Product(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4,editable=False,unique=True)
    product_name = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(max_length=200, unique=True)
    base_price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField()
    is_listed = models.BooleanField(default=True) 
    category = models.ForeignKey(Category, on_delete=models.CASCADE,related_name='products')
    image = models.ImageField(upload_to='products/')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)
    is_available = models.BooleanField(default=True)
    is_blocked = models.BooleanField(default=False)
    offer_price = models.DecimalField(max_digits=10,decimal_places=2,null=True,blank=True)
    brand = models.CharField(max_length=100, default='Lotto')

    @property
    def total_stock(self):
        return sum(variant.stock for variant in self.variants.all())

    @property
    def discount_percentage(self): 
        if self.offer_price and self.base_price > 0:
            return int(((self.base_price - self.offer_price) / self.base_price) * 100 )
        return 0

    def __str__(self):
        return self.product_name

    def get_discounted_price(self):
        base_price = self.base_price
        product_discount = Decimal('0.00')
        category_discount = Decimal('0.00')

        # Check Product Offer
        if hasattr(self, 'product_offers') and self.product_offer.is_active:
            offer = self.product_offer
            if offer.discount_percentage > 0:
                product_discount = base_price * Decimal(offer.discount_percentage) / Decimal(100)
            elif offer.discount_amount > 0:
                product_discount = min(offer.discount_amount, base_price)

        # Check Category Offer
        if self.category and hasattr(self.category, 'category_offers') and self.category.category_offer.is_active:
            c_offer = self.category.category_offer
            if c_offer.discount_percentage > 0:
                category_discount = base_price * Decimal(c_offer.discount_percentage) / Decimal(100)
            elif c_offer.discount_amount > 0:
                category_discount = min(c_offer.discount_amount, base_price)

        # Apply the largest discount
        max_discount = max(product_discount, category_discount)
        if max_discount > 0:
            return (base_price - max_discount).quantize(Decimal('0.01'))
        return base_price


class ProductOffer(models.Model):
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name='product_offer')
    discount_percentage = models.PositiveIntegerField(help_text="Discount percentage (e.g. 10 for 10%)", default=0)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Offer on {self.product.product_name}"


class CategoryOffer(models.Model):
    category = models.OneToOneField(Category, on_delete=models.CASCADE, related_name='category_offer')
    discount_percentage = models.PositiveIntegerField(help_text="Discount percentage (e.g. 15 for 15%)", default=0)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Offer on {self.category.name}"


def recalculate_product_offer_price(product):
    base_price = product.base_price
    product_discount = Decimal('0.00')
    category_discount = Decimal('0.00')

    # Product offer check
    try:
        offer = ProductOffer.objects.get(product=product, is_active=True)
        if offer.discount_percentage > 0:
            product_discount = base_price * Decimal(offer.discount_percentage) / Decimal(100)
        elif offer.discount_amount > 0:
            product_discount = min(offer.discount_amount, base_price)
    except ProductOffer.DoesNotExist:
        pass

    # Category offer check
    if product.category:
        try:
            c_offer = CategoryOffer.objects.get(category=product.category, is_active=True)
            if c_offer.discount_percentage > 0:
                category_discount = base_price * Decimal(c_offer.discount_percentage) / Decimal(100)
            elif c_offer.discount_amount > 0:
                category_discount = min(c_offer.discount_amount, base_price)
        except CategoryOffer.DoesNotExist:
            pass

    max_discount = max(product_discount, category_discount)
    if max_discount > 0:
        new_offer_price = (base_price - max_discount).quantize(Decimal('0.01'))
    else:
        new_offer_price = None

    # Update database directly to avoid infinite save signal recursion
    Product.objects.filter(pk=product.pk).update(offer_price=new_offer_price)


@receiver([post_save, post_delete], sender=ProductOffer)
def product_offer_change(sender, instance, **kwargs):
    recalculate_product_offer_price(instance.product)


@receiver([post_save, post_delete], sender=CategoryOffer)
def category_offer_change(sender, instance, **kwargs):
    products = instance.category.products.all()
    for product in products:
        recalculate_product_offer_price(product)


@receiver(post_save, sender=Product)
def product_base_price_change(sender, instance, created=False, **kwargs):
    # Recalculate on product price changes, but check if we're not inside update recursion.
    # Note: Product.objects.update doesn't trigger post_save, so it's safe.
    recalculate_product_offer_price(instance)

    

class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='products/gallery/')

    def __str__(self):
        return self.product.product_name
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        img = Image.open(self.image.path)

        width, height = img.size
        min_dim = min(width,height)

        left = (width - min_dim) // 2
        top = (height - min_dim) // 2
        right = (width + min_dim)
        bottom = (width + min_dim)

        img = img.crop((left,top,right,bottom))
        img = img.resize((500, 500))

        img.save(self.image.path)



class ProductVariant(models.Model):
    SIZE_CHOICES = [
        ('7', '7'),
        ('8', '8'),
        ('9', '9'),
        ('10', '10'),
        ('11', '11'),
        ('12', '12'),
    ]
  
    uuid = models.UUIDField(default=uuid.uuid4,unique=True,editable=False)
    product = models.ForeignKey(Product,on_delete=models.CASCADE,related_name='variants')
    size = models.CharField(max_length=20, choices=SIZE_CHOICES)
    color = models.CharField(max_length=50)
    stock = models.PositiveIntegerField(default=0)
    price = models.DecimalField(max_digits=10,decimal_places=2)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.product.product_name} - {self.size} - {self.color}"
    
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['product', 'size', 'color'],
                name='unique_product_variant'
            )
        ]



    

