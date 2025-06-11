from accounts.models import Account
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils import timezone

from store.models import Product,Variation


# Create your models here.
class Promotion(models.Model):
    promotion_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, help_text="Promotion name for admin reference")
    quantity = models.PositiveIntegerField(help_text="Available quantity for this promotion")
    discount_code = models.CharField(max_length=50, unique=True, help_text="Code users enter at checkout")
    discount_value = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Discount percentage (0-100)"
    )
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    manager = models.ForeignKey(
        Account,
        on_delete=models.SET_NULL,
        null=True,
        limit_choices_to={'role': 3},  # Chỉ Manager
        related_name='managed_promotions'
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        db_table = 'promotion'
        ordering = ['-created_at']

    def __str__(self):
        return f"Promotion: {self.discount_code} ({self.discount_value}%)"

    @property
    def is_valid(self):
        """Check if promotion is currently valid"""
        now = timezone.now()
        return (
                self.is_active and
                self.start_date <= now <= self.end_date and
                self.quantity > 0
        )
    def can_be_used_by_user(self, user):
        """Check if user can use this promotion"""
        if not self.is_valid:
            return False, "Promotion is not valid"

        # Check if user already used this promotion
        if UserHavePromotion.objects.filter(user=user, promotion=self).exists():
            return False, "You have already used this promotion"

        return True, "Promotion can be used"


class UserHavePromotion(models.Model):
    user = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='used_promotions')
    promotion = models.ForeignKey(Promotion, on_delete=models.CASCADE, related_name='users_used')
    used_at = models.DateTimeField(auto_now_add=True)
    order = models.ForeignKey('Order', on_delete=models.SET_NULL, null=True, blank=True)  # Track which order used it
    class Meta:
        db_table = 'user_have_promotion'
        unique_together = ('user', 'promotion')
        verbose_name = 'User Promotion Usage'
        verbose_name_plural = 'User Promotion Usages'

    def __str__(self):
        return f"{self.user.email} used {self.promotion.discount_code}"


class Payment(models.Model):

    PAYMENT_STATUS = (
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed')
    )
    PAYMENT_METHOD = (
        ('Momo', 'Momo'),
        ('cash', 'Cash on delivery'),
    )
    user = models.ForeignKey(Account, on_delete=models.CASCADE)
    payment_id = models.CharField(max_length=100, unique=True)
    payment_method = models.CharField(max_length=100)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=100, choices=PAYMENT_STATUS, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment #{self.payment_id} - ({self.status})"


class Order(models.Model):
    ORDER_STATUS = (
        ('Pending', 'Pending'),
        ('processing', 'Processing'),
        ('Shipped', 'Shipped'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
    )
    user = models.ForeignKey(Account, on_delete=models.CASCADE)
    payment = models.ForeignKey(Payment, on_delete=models.SET_NULL, blank = True, null=True)
    first_name = models.CharField(max_length=50,default='')
    last_name = models.CharField(max_length=50,default='')
    phone = models.CharField(max_length=15,default='')
    email = models.EmailField(max_length=50, default='')
    shipping_address = models.TextField()
    order_number = models.CharField(max_length=100, unique=True)
    order_discount = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, blank=True,validators=[MinValueValidator(0)]
    )
    promotion_used = models.ForeignKey(
        Promotion,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders_used_in'
    )
    order_note = models.TextField(blank=True)
    order_total = models.DecimalField(max_digits=10, decimal_places=2)
    order_status = models.CharField(max_length=100, choices=ORDER_STATUS, default='Pending')
    is_ordered = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    staff = models.ForeignKey(
        Account,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'role': 2},  # only staff
        related_name='processed_orders',
        verbose_name='StaffProcessing'
    )



    def __str__(self):
        return f"Order #{self.order_number} - {self.order_status}"





class OrderProduct(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    payment = models.ForeignKey(Payment, on_delete=models.SET_NULL, blank=True, null=True)
    user = models.ForeignKey(Account, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variations = models.ManyToManyField(Variation, blank=True)
    quantity = models.IntegerField(validators=[MinValueValidator(1)])
    product_price = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )
    ordered = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.quantity} x {self.product.name} (Order #{self.order.order_number})"

    def save(self, *args, **kwargs):
        # Calculate subtotal
        if not self.subtotal:
            self.subtotal = self.quantity * self.product_price

