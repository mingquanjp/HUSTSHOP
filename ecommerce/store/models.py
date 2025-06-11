from platform import system

from django.db import models
from django.db.models import Count, Avg
from django.urls import reverse

from accounts.models import Account

from reviews.models import Review


# Create your models here.
class Category(models.Model):
    name = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(max_length=200, unique=True)
    description = models.TextField(blank=True)
    manager = models.ForeignKey(
        Account,
        on_delete=models.SET_NULL,
        null=True,
        limit_choices_to={'role': 3},  # Chỉ cho phép Manager
        related_name='managed_categories'
    )

    #system
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'
        ordering = ['name']

    def __str__(self):
        return self.name


    def get_url(self):
        return reverse('products_by_category', args=[self.slug])

class Product(models.Model):
    name = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(max_length=200, unique=True)
    description = models.TextField(max_length=500, blank=True)
    image = models.ImageField(upload_to='uploads/products', blank=True)
    price = models.IntegerField(default=0)
    stock = models.PositiveIntegerField()
    is_available = models.BooleanField(default=True)
    star_rated = models.DecimalField(max_digits=5, decimal_places=1, default=0.0)
    category = models.ForeignKey( #Xoa category thi product auto xoa
        Category,
        on_delete=models.CASCADE,
        related_name='products'
    )



    manager = models.ForeignKey(
        Account,
        on_delete=models.SET_NULL,
        null=True,
        limit_choices_to={'role': 3},  # Chỉ Manager
        related_name='managed_products'
    )


    #system
    created_at = models.DateTimeField(auto_now_add=True,verbose_name='Created At')
    updated_at = models.DateTimeField(auto_now=True,verbose_name='Updated At')

    def __str__(self):
        return self.name

    def get_url(self):
        return reverse('product_detail', args=[self.category.slug, self.slug])

    def averageReview(self):
        reviews = Review.objects.filter(product=self, status=True).aggregate(average=Avg('rating'))
        avg = 0
        if reviews['average'] is not None:
            avg = float(reviews['average'])
        return avg

    def countReview(self):
        reviews = Review.objects.filter(product=self, status=True).aggregate(count=Count('id'))
        count = 0
        if reviews['count'] is not None:
            count = int(reviews['count'])
        return count


    def formatted_price(self):
        return f"{self.price:,} VND"




    class Meta:
        verbose_name = 'Product'
        verbose_name_plural = 'Products'
        ordering = ['-created_at']
        #Indexed
        indexes = [
            models.Index(fields=['id', 'slug']),
            models.Index(fields=['name']),
            models.Index(fields=['-created_at']),
        ]


class VariationManager(models.Manager):
    def color(self):
        return super(VariationManager, self).filter(variation_category='color', is_active=True)
    def size(self):
        return super(VariationManager,self).filter(variation_category='size', is_active=True)

variation_category_choices = (
    ('color', 'color'),
    ('size', 'size'),
)


class Variation(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variations')
    variation_category = models.CharField(max_length=100, choices=variation_category_choices)
    variation_value = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = VariationManager()

    def __str__(self):
        return self.variation_value











from django.db import models

# Create your models here.
