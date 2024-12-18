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


class CreateOrderProductView(LoginRequiredMixin, CreateView):
    template_name = "orders/create_order_product.html"
    form_class = OrderProductForm
    success_url = reverse_lazy("my_order")

    def form_valid(self, form):
        # Buscar o crear una orden activa para el usuario
        order, _ = Order.objects.get_or_create(is_active=True, user=self.request.user)
        # Asignar la orden al formulario
        form.instance.order = order
        form.instance.quantity = int(self.request.POST.get("quantity", 1))
        product = form.instance.product  # Producto desde el formulario

        # Verificar si el producto ya existe en la orden
        order_product, create = OrderProduct.objects.get_or_create(
            order=order, product=product
        )
        if create:
            # Si es nuevo, establecer la cantidad inicial
            # order_product.quantity = form.cleaned_data.get('quantity', 1)
            order_product.quantity = int(self.request.POST.get("quantity", 1))
            messages.success(self.request, "The product has been added to order")
        else:
            # Si ya existe, incrementar la cantidad
            order_product.quantity += int(self.request.POST.get("quantity", 1))
            messages.success(
                self.request, "The quantity product has been update on to order."
            )

        order_product.save()
        # form.save()
        return super().form_invalid(form)


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
        product.delete()
        messages.success(request, "The product has been to deleted successfully.")
    return redirect(reverse("my_order"))
    #   return JsonResponse({'success': True, 'message': "The product has been to deleted successfully."})
    # return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=400)
