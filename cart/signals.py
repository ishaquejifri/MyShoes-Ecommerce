from django.db.models.signals import post_save
from django.dispatch import receiver
from accounts.models import CustomUser
from .models import Cart


@receiver(post_save,sender=CustomUser)
def create_cart(sender,instance,created,**kwargs):
    if created:
        Cart.objects.create(user=instance)

        
