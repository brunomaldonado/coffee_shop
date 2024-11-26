from django.urls import path
from .views import MyOrderView, CreateOrderProductView, delete_product, update_cart

urlpatterns = [
    path("my-order", MyOrderView.as_view(), name="my_order"),
    path("add-product", CreateOrderProductView.as_view(), name="add_product"),
    path("update-cart/", update_cart, name="update_cart"),
    path("delete-product/<int:product_id>", delete_product, name="delete_product"),
]
