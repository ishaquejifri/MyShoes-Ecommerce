from django.db import models

class Banner(models.Model):
    BANNER_TYPES = (
        ('hero', 'Hero Banner'),
        ('offer', 'Offer Banner'),
        ('category', 'Category Banner'),
    )

    title = models.CharField(max_length=200)
    subtitle = models.CharField(max_length=255, blank=True, null=True)
    image = models.ImageField(upload_to='banners/')
    button_text = models.CharField(max_length=100, blank=True, null=True)
    button_link = models.CharField(max_length=255, blank=True, null=True)

    banner_type = models.CharField(max_length=20, choices=BANNER_TYPES, default='hero')
    display_order = models.PositiveIntegerField(default=0)

    is_active = models.BooleanField(default=True)

    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['display_order']

    def __str__(self):
        return self.title

