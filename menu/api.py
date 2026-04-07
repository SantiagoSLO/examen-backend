from rest_framework import generics
from .models import Categoria, Producto
from .serializers import CategoriaSerializer, ProductoSerializer


class CategoriaListCreateView(generics.ListCreateAPIView):
    queryset = Categoria.objects.filter(activa=True)
    serializer_class = CategoriaSerializer


class CategoriaDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer


class ProductoListCreateView(generics.ListCreateAPIView):
    queryset = Producto.objects.filter(disponible=True)
    serializer_class = ProductoSerializer


class ProductoDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Producto.objects.all()
    serializer_class = ProductoSerializer