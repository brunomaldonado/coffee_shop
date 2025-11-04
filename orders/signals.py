from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from .models import Order, OrderProduct
from products.models import Product


@receiver(user_logged_in)
def sync_cart_on_login(sender, request, user, **kwargs):
  """Sincronizar carrito de sesión con orden del usuario al hacer login"""

  # Obtener carrito de sesión
  cart = request.session.get('cart', {})

  if not cart:
    return  # No hay nada que sincronizar

  try:
    # Obtener o crear orden activa del usuario
    order, _ = Order.objects.get_or_create(is_active=True, user=user)

    # Agregar productos del carrito de sesión a la orden
    for product_id, item in cart.items():
      try:
        product = Product.objects.get(id=int(product_id))
        quantity = item['quantity']

        # Obtener o crear el producto en la orden
        order_product, created = OrderProduct.objects.get_or_create(
          order=order,
          product=product,
          defaults={'quantity': quantity}
        )

        if not created:
          # Si ya existía, sumar las cantidades
          order_product.quantity += quantity
          if order_product.quantity > 5:
            order_product.quantity = 5
          order_product.save()

        print(f"[SYNC] Product {product.name} synced to order")

      except Product.DoesNotExist:
        print(f"[SYNC] Product {product_id} not found")
        continue

    # Limpiar carrito de sesión
    request.session['cart'] = {}
    request.session.modified = True

    print(f"[SYNC] Cart synced successfully for user {user.username}")

  except Exception as e:
    print(f"[SYNC ERROR] {str(e)}")
