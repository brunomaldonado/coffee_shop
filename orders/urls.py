from django.urls import path
from .views import MyOrderView, AddToOrderView, delete_product, update_cart, get_order_count

urlpatterns = [
    path('my-order', MyOrderView.as_view(), name='my_order'),
    path('add-order', AddToOrderView.as_view(), name='add_to_order'),
    path('order-count/', get_order_count, name='get_order_count'),
    path('update-cart/', update_cart, name='update_cart'),
    path('delete-product/<int:product_id>/', delete_product, name='delete_product'),
]
