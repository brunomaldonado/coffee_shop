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
    success_url = reverse_lazy('list_products')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({
            'files': self.request.FILES or None
        })
        return kwargs

    def form_valid(self, form):
        form.save()

        return super().form_valid(form)


class ProductListView(generic.ListView):
    model = Product
    template_name = "products/list_products.html"
    context_object_name = "products"


# class ProductListAPI(APIView):
#     authentication_classes = []
#     permission_classes = []

#     def get(self, request):
#         products = Product.objects.all()
#         serializer = ProductSerializer(products, many=True)
#         return Response(serializer.data)  # data configurada en formato JSON
