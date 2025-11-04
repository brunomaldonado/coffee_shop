from .models import Order

def cart_count(request):
    if request.user.is_authenticated:
        try:
          order = Order.objects.filter(is_active=True, user=request.user).first()
          count = order.orderproduct_set.count() if order else 0
        except Order.DoesNotExist:
            count = 0
    else:
      count = len(request.session.get('cart', {}))
    return {'cart_count': count}
