from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from decimal import Decimal
import random
import string

class CustomUser(AbstractUser):
    phone = models.CharField(max_length=15,null=True,blank=True)
    is_block = models.BooleanField(default=False)
    otp = models.CharField(max_length=6, null=True, blank=True)
    otp_created_at = models.DateTimeField(null=True, blank=True)
    profile_image = models.ImageField(upload_to='profile_images/',blank=True,null=True)
    
    referral_code = models.CharField(max_length=20, unique=True, null=True, blank=True)
    referred_by = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='referrals')

    def __str__(self):
        return self.username 
    

class Address(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name='addresses')
    full_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    address_line = models.TextField()
    street = models.CharField(max_length=50)
    city = models.CharField(max_length=50)
    state = models.CharField(max_length=50)
    postal_code = models.CharField(max_length=10)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.full_name} - {self.city}"


class Wallet(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='wallet')
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Wallet - ₹{self.balance}"

    def deposit(self, amount, description="Deposit", transaction_type='deposit', order=None):
        amount = Decimal(str(amount))
        self.balance += amount
        self.save()
        WalletTransaction.objects.create(
            wallet=self,
            amount=amount,
            transaction_type=transaction_type,
            description=description,
            order=order
        )

    def withdraw(self, amount, description="Withdrawal", transaction_type='withdrawal', order=None):
        amount = Decimal(str(amount))
        if self.balance < amount:
            raise ValueError("Insufficient balance")
        self.balance -= amount
        self.save()
        WalletTransaction.objects.create(
            wallet=self,
            amount=amount,
            transaction_type=transaction_type,
            description=description,
            order=order
        )


class WalletTransaction(models.Model):
    TRANSACTION_TYPES = [
        ('deposit', 'Deposit'),
        ('withdrawal', 'Withdrawal'),
        ('refund', 'Refund'),
        ('payment', 'Payment'),
        ('referral_reward', 'Referral Reward'),
    ]
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='transactions')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_type = models.CharField(max_length=25, choices=TRANSACTION_TYPES)
    description = models.TextField(blank=True, null=True)
    order = models.ForeignKey('orders.Order', on_delete=models.SET_NULL, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.transaction_type.capitalize()} of ₹{self.amount} on {self.timestamp}"


@receiver(post_save, sender=CustomUser)
def create_user_wallet_and_referral(sender, instance, created, **kwargs):
    if created:
        # Generate unique referral code
        clean_username = "".join([c for c in instance.username if c.isalnum()]).upper()
        prefix = clean_username[:5] if len(clean_username) >= 5 else clean_username
        code = prefix
        attempts = 0
        while not code or CustomUser.objects.filter(referral_code=code).exists() or len(code) < 8:
            random_suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=max(3, 8 - len(prefix))))
            code = f"{prefix}{random_suffix}"
            attempts += 1
            if attempts > 100:
                code = "".join(random.choices(string.ascii_uppercase + string.digits, k=10))
                break
        
        instance.referral_code = code
        instance.save(update_fields=['referral_code'])

        # Create Wallet
        Wallet.objects.get_or_create(user=instance)