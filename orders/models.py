from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from products.models import Product


class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    order_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=['user', 'is_active'])]

    def __str__(self):
        return f"Order {self.id} by {self.user}"


class OrderProduct(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)

    class Meta:
        indexes = [models.Index(fields=['order', 'product'])]
        unique_together = ('order', 'product')

    def clean(self):
        if self.quantity < 1:
            raise ValidationError("The minimum quantity is 1.")
        if self.quantity > 5:
            raise ValidationError("The maximum count allowed is 5.")

    def save(self, *args, **kwargs):
        self.clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.order} - {self.product}"
