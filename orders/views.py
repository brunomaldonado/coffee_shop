from IPython.core.magic_arguments import defaults
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import DetailView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from .models import Order, OrderProduct
from .forms import OrderProductForm
from django.urls import reverse
from decimal import Decimal
from django.views import View
from django.shortcuts import render, redirect
from django.core.exceptions import ValidationError
import time
import sys
import io

# Configurar UTF-8 para Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


class MyOrderView(LoginRequiredMixin, DetailView):
    model = Order
    template_name = "orders/my_order.html"
    context_object_name = "order"

    def get_object(self, queryset=None):
        # Retorna la primera orden activa del usuario o None si no existe
        return Order.objects.filter(is_active=True, user=self.request.user).first()

    def get_context_data(self, **kwargs):
        # Obtener el contexto original del DetailView
        context = super().get_context_data(**kwargs)

        # Obtener el objeto `order`
        order = self.get_object()

        # Si no hay orden activa, agregar un mensaje al contexto y devolverlo
        if order is None:
            context["items"] = []
            context["subtotal"] = 0
            context["tax"] = 0
            context["total"] = 0
            context["message"] = "You do not have any products in you order."
            return context

        # Obtener los productos relacionados a la orden
        items = order.orderproduct_set.all()
        item_details = []
        subtotal = 0

        for item in items:
            total_price_per_item = float(item.product.price * item.quantity)
            item_details.append(
                {
                    "id": item.id,
                    "product_name": item.product.name,
                    "quantity": item.quantity,
                    "price": item.product.price,
                    "total_price": total_price_per_item,
                }
            )
            subtotal += total_price_per_item
            tax = subtotal * 0.16
            total = subtotal + tax

            # Agregar los detalles al contexto
            context["items"] = item_details
            context["subtotal"] = f"{subtotal:.2f}"
            context["tax"] = f"{tax:.2f}"
            context["total"] = f"{total:.2f}"

        return context


class AddToOrderView(View):
    def post(self, request, *args, **kwargs):
        start = time.time()

        form = OrderProductForm(request.POST)

        if form.is_valid():
            try:
                product = form.cleaned_data['product']
                quantity = form.cleaned_data['quantity']

                # âœ… Si el usuario estÃ¡ autenticado
                if request.user.is_authenticated:
                    t1 = time.time()
                    order, _ = Order.objects.get_or_create(
                        is_active=True,
                        user=request.user
                    )
                    print(f"[TIME] get_or_create Order: {time.time() - t1:.3f}s")

                    t2 = time.time()
                    order_product, created = OrderProduct.objects.get_or_create(
                        order=order,
                        product=product,
                        defaults={'quantity': quantity}
                    )
                    print(f"[TIME] get_or_create OrderProduct: {time.time() - t2:.3f}s")

                    if created:
                        message = "The product has been added to order"
                        is_new = True
                    else:
                        order_product.quantity += quantity
                        if order_product.quantity > 5:
                            order_product.quantity = 5
                            message = "Maximum quantity (5) reached"
                        else:
                            message = "The quantity has been updated"
                        order_product.save()
                        is_new = False

                    cart_count = order.orderproduct_set.count()
                    print(f"[TOTAL] Total time: {time.time() - start:.3f}s")

                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({
                            'success': True,
                            'message': message,
                            'is_new': is_new,
                            'cart_count': cart_count,
                            'current_quantity': order_product.quantity
                        })

                    return redirect('my_order')

                # âœ… Si NO estÃ¡ autenticado - guardar en sesiÃ³n
                else:
                    if 'cart' not in request.session:
                        request.session['cart'] = {}

                    product_id = str(product.id)
                    cart = request.session['cart']

                    if product_id in cart:
                        cart[product_id]['quantity'] += quantity
                        if cart[product_id]['quantity'] > 5:
                            cart[product_id]['quantity'] = 5
                            message = "Maximum quantity (5) reached"
                        else:
                            message = "The quantity has been updated"
                        is_new = False
                    else:
                        cart[product_id] = {
                            'quantity': quantity,
                            'name': product.name,
                            'price': str(product.price)
                        }
                        message = "The product has been added to cart"
                        is_new = True

                    request.session.modified = True
                    cart_count = len(cart)

                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({
                            'success': True,
                            'message': message,
                            'is_new': is_new,
                            'cart_count': cart_count,
                            'requires_login': True  # âœ… Indicador para el frontend
                        })

                    # Si no es AJAX, redirigir al login
                    return redirect(f'/login/?next={request.path}')

            except ValidationError as e:
                print(f"[ERROR] Validation error: {str(e)}")
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False,
                        'error': str(e)
                    }, status=400)
                return render(request, "orders/add_to_order.html", {'form': form})

            except Exception as e:
                print(f"[ERROR] Exception: {str(e)}")
                import traceback
                traceback.print_exc()

                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False,
                        'error': 'An error occurred while adding the product'
                    }, status=500)
                return render(request, "orders/add_to_order.html", {'form': form})

        else:
            print(f"[ERROR] Form errors: {form.errors}")

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'errors': form.errors
                }, status=400)

            return render(request, "orders/add_to_order.html", {'form': form})

# class AddToOrderView(LoginRequiredMixin, CreateView):
#     template_name = "orders/add_to_order.html"
#     form_class = OrderProductForm
#     success_url = reverse_lazy("my_order")
#
#
#     def post(self, request, *args, **kwargs):
#         start = time.time()
#         print("enter default")
#
#
#         # if not request.user.is_authenticated:
#         #     if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
#         #         return JsonResponse({
#         #             'success': False,
#         #             'error': 'Authentication required'
#         #         }, status=401)
#
#         form = OrderProductForm(request.POST)
#
#         if form.is_valid():
#             try:
#                 t1 = time.time()
#                 # Buscar o crear una orden activa
#                 order, _ = Order.objects.get_or_create(is_active=True, user=request.user)
#                 print(f"[TIME] get_or_create Order: {time.time() - t1:.3f} seconds")
#
#                 t2 = time.time()
#                 product = form.cleaned_data['product']
#                 quantity = form.cleaned_data['quantity']
#                 print(f"[TIME] Get form data: {time.time() - t2:.3f} seconds")
#
#                 t3 = time.time()
#                 # Obtener o crear OrderProduct
#                 order_product, created = OrderProduct.objects.get_or_create(
#                     order=order,
#                     product=product,
#                     defaults={'quantity': quantity}
#                 )
#                 print(f"[TIME] get_or_create OrderProduct: {time.time() - t3:.3f} seconds")
#
#                 t4 = time.time()
#                 if created:
#                     # âœ… Producto nuevo
#                     message = "The product has been added to order"
#                     is_new = True
#                 else:
#                     # âœ… Producto existente - incrementar cantidad
#                     order_product.quantity += quantity
#
#                     if order_product.quantity > 5:
#                         order_product.quantity = 5
#                         message = "Maximum quantity (5) reached"
#                     else:
#                         message = "The quantity has been updated"
#
#                     order_product.save()  # Solo guardamos si no es nuevo
#                     is_new = False
#
#                 print(f"[TIME] Save quantity: {time.time() - t4:.3f} seconds")
#
#                 t5 = time.time()
#                 cart_count = order.orderproduct_set.count()
#                 print(f"[TIME] Count products: {time.time() - t5:.3f}s")
#                 print(f"[TOTAL] Total time: {time.time() - start:.3f}s")
#
#                 # Respuesta para AJAX
#                 if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
#                     return JsonResponse({
#                         'success': True,
#                         'message': message,
#                         'is_new': is_new,
#                         'cart_count': cart_count,
#                         'current_quantity': order_product.quantity
#                     })
#
#                 return redirect('my_order')
#
#             except ValidationError as e:
#                 print(f"[ERROR] Validation error: {str(e)}")
#                 if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
#                     return JsonResponse({
#                         'success': False,
#                         'error': str(e)
#                     }, status=400)
#                 return render(request, "orders/add_to_order.html", {'form': form})
#
#             except Exception as e:
#                 print(f"[ERROR] Exception: {str(e)}")
#                 import traceback
#                 traceback.print_exc()
#
#                 if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
#                     return JsonResponse({
#                         'success': False,
#                         'error': 'An error occurred while adding the product'
#                     }, status=500)
#                 return render(request, "orders/add_to_order.html", {'form': form})
#
#         else:
#             # Formulario invÃ¡lido
#             print(f"[ERROR] Form errors: {form.errors}")
#
#             if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
#                 return JsonResponse({
#                     'success': False,
#                     'errors': form.errors
#                 }, status=400)
#
#             return render(request, "orders/add_to_order.html", {'form': form})


# class AddToOrderView(LoginRequiredMixin, View):
#     def get(self, request):
#         form = OrderProductForm()
#         return render(request, "orders/add_to_order.html", {'form': form})
#
#     def post(self, request):
#         start = time.time()
#
#         # Verificar autenticaciÃ³n para AJAX
#         if not request.user.is_authenticated:
#             if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
#                 return JsonResponse({
#                     'success': False,
#                     'error': 'Authentication required'
#                 }, status=401)
#
#         form = OrderProductForm(request.POST)
#
#         if form.is_valid():
#             try:
#                 t1 = time.time()
#                 # Obtener o crear orden activa
#                 order, _ = Order.objects.get_or_create(
#                     is_active=True,
#                     user=request.user
#                 )
#                 print(f" get_or_create Order: {time.time() - t1:.3f} seconds")
#
#                 t2 = time.time()
#                 product = form.cleaned_data['product']
#                 quantity = form.cleaned_data['quantity']
#                 print(f" Get form data: {time.time() - t2:.3f} seconds")
#
#                 t3 = time.time()
#                 # Obtener o crear OrderProduct
#                 order_product, created = OrderProduct.objects.get_or_create(
#                     order=order,
#                     product=product,
#                     defaults={'quantity': quantity}
#                 )
#                 print(f" get_or_create OrderProduct: {time.time() - t3:.3f} seconds")
#
#                 t4 = time.time()
#                 if created:
#                     message = "The product has been added to order"
#                     is_new = True
#                 else:
#                     # Si ya existe, incrementar cantidad
#                     order_product.quantity += quantity
#
#                     # Validar lÃ­mite mÃ¡ximo
#                     if order_product.quantity > 5:
#                         order_product.quantity = 5
#                         message = "Maximum quantity (5) reached"
#                     else:
#                         message = "The quantity has been updated"
#
#                     order_product.save()
#                     is_new = False
#
#                 print(f" Save quantity: {time.time() - t4:.3f} seconds")
#
#                 t5 = time.time()
#                 cart_count = order.orderproduct_set.count()
#                 print(f" Count products: {time.time() - t5:.3f}s")
#                 print(f" TOTAL TIME: {time.time() - start:.3f}s")
#
#                 # Respuesta para AJAX
#                 if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
#                     return JsonResponse({
#                         'success': True,
#                         'message': message,
#                         'is_new': is_new,
#                         'cart_count': cart_count,
#                         'current_quantity': order_product.quantity
#                     })
#
#                 # Respuesta para form tradicional
#                 return redirect('my_order')
#
#             except ValidationError as e:
#                 if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
#                     return JsonResponse({
#                         'success': False,
#                         'error': str(e)
#                     }, status=400)
#                 return render(request, self.template_name, {'form': form})
#
#             except Exception as e:
#                 print(f" Error: {e}")
#                 import traceback
#                 traceback.print_exc()  # Ver el error completo en consola
#
#                 if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
#                     return JsonResponse({
#                         'success': False,
#                         'error': 'An error occurred while adding the product'
#                     }, status=500)
#                 return render(request, self.template_name, {'form': form})
#
#         else:
#             # Formulario invÃ¡lido
#             print(f" Form errors: {form.errors}")
#
#             if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
#                 return JsonResponse({
#                     'success': False,
#                     'errors': form.errors
#                 }, status=400)
#
#             return render(request, "orders/add_to_order.html", {'form': form})

def get_order_count(request):
    if request.user.is_authenticated:
        order = Order.objects.filter(is_active=True, user=request.user).first()
        count = order.orderproduct_set.all() if order else 0
    else:
        count = len(request.session.get('cart', {}))

    return JsonResponse({'cart_count': count})

@csrf_exempt
def update_cart(request):
    if request.method == "POST":
        data = json.loads(request.body)
        product_id = data.get("product_id")
        new_quantity = int(data.get("quantity"))

        # Obtener la orden activa
        order = Order.objects.filter(is_active=True, user=request.user).first()

        if order:
            # Buscar el producto en la orden y actualizar la cantidad
            order_product = order.orderproduct_set.filter(id=product_id).first()
            if order_product:
                order_product.quantity = new_quantity
                order_product.save()

            # Calcular el subtotal, IGV y total
            items = order.orderproduct_set.all()
            subtotal = sum([item.product.price * item.quantity for item in items])
            tax = subtotal * Decimal("0.16")
            total = subtotal + tax

            # Enviar los nuevos valores como respuesta JSON
            return JsonResponse(
                {
                    "total_price_per_item": f"{order_product.product.price * order_product.quantity:.2f}",
                    "subtotal": f"{subtotal:.2f}",
                    "tax": f"{tax:.2f}",
                    "total": f"{total:.2f}",
                }
            )

    return JsonResponse({"error": "Invalid request"}, status=400)


def delete_product(request, product_id):
    product = get_object_or_404(OrderProduct, id=product_id, order__user=request.user)
    if request.method == "POST":
        order = product.order
        product.delete()

        # if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.content_type == 'application/json':
            # Recalcular subtotal, tax y total
        order_products = order.orderproduct_set.all()
        cart_count = order_products.count()

        if order_products.exists():
            subtotal = sum([Decimal(str(item.product.price)) * item.quantity for item in order_products])
            tax = subtotal * Decimal("0.16")
            total = subtotal + tax
        else:
            subtotal = tax = total = Decimal("0.00")


        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.content_type == 'application/json':
            return JsonResponse({
                'success': True,
                'message': 'Product deleted successfully',
                'subtotal': f"{subtotal:.2f}",
                'tax': f"{tax:.2f}",
                'total': f"{total:.2f}",
                'cart_count': cart_count,
                'has_products': order_products.exists()
            })
        # else:
        messages.success(request, "The product has been removed from the order.")
        return redirect(reverse("my_order"))
    return redirect(reverse("my_order"))
