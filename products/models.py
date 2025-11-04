from django.db import models

class Product(models.Model):
    name = models.TextField(max_length=250, verbose_name="Name")
    description = models.TextField(max_length=300, verbose_name="Description")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Price")
    available = models.BooleanField(default=True, verbose_name="Available")
    image = models.ImageField(upload_to='products', default='assets/image_not_available.png', null="True", blank="True", verbose_name="Image")

    def __str__(self):
        return self.name


class CartItem(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} of {self.product.name}"
