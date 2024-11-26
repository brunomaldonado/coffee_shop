from django.http import HttpResponse
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views import generic

from .forms import ProductForm
from products.models import Product
from .models import CartItem, Product

from rest_framework.views import APIView
from .serializers import ProductSerializer
from rest_framework.response import Response


class ProductFormView(generic.FormView):
    template_name = "products/add_product.html"
    form_class = ProductForm
    success_url = reverse_lazy("add_product")

    def form_valid(self, form):
        quantity = int(self.request.POST.get("quantity", 1))
        product_id = form.instance.product  # Producto desde el formulario

        # Verificar si el producto ya existe en la orden
        cart_item, created = CartItem.objects.get_or_create(
            product=product_id, quantity=quantity
        )

        if not created:
            cart_item.quantity += quantity
            cart_item.save()

            # Puedes retornar una respuesta o redirigir a alguna página
            return JsonResponse(
                {
                    "message": "Producto agregado al carrito",
                    "total_quantity": cart_item.quantity,
                }
            )

        # Si no hay acción de carrito, continuar normalmente con el guardado
        cart_item.save()
        return super().form_valid(form)


class ProductListView(generic.ListView):
    model = Product
    template_name = "products/list_products.html"
    context_object_name = "products"


class ProductListAPI(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        products = Product.objects.all()
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)  # data configurada en formato JSON
