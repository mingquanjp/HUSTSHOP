from accounts.models import Account
from django.db import models

from store.models import Product, Variation


class Cart(models.Model):
    cart_id = models.CharField(max_length=250, blank=True)
    user = models.ForeignKey(Account, on_delete=models.CASCADE, null=True,blank=True)
    date_added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.user:
            return f"Cart của {self.user.email}"
        return f"Anonymous Cart: {self.cart_id[:20]}..."

    class Meta:
        # Đảm bảo mỗi user chỉ có 1 cart
        constraints = [
            models.UniqueConstraint(
                fields=['user'],
                condition=models.Q(user__isnull=False),
                name='unique_user_cart'
            )
        ]


class CartItem(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variations = models.ManyToManyField(Variation, blank=True)
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, null=True)
    quantity = models.IntegerField()
    is_active = models.BooleanField(default=True)

    def sub_total(self):
        return self.quantity * self.product.price

    def __unicode__(self):
        return self.product

# Create your models here.
