from django.db import models
import uuid

# Create your models here.
class Category(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    image = models.ImageField(upload_to='category/',null=True,blank=True)
    name = models.CharField(max_length=100,unique=True)
    description = models.TextField(blank=True,null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
    
    