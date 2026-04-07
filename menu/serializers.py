from rest_framework import serializers
from .models import Categoria, Producto


class CategoriaSerializer(serializers.ModelSerializer):
    productos_count = serializers.SerializerMethodField()

    class Meta:
        model = Categoria
        fields = ['id', 'nombre', 'descripcion', 'orden', 'activa', 'imagen', 'fecha_creacion', 'productos_count']

    def get_productos_count(self, obj):
        return obj.get_productos_count()


class ProductoSerializer(serializers.ModelSerializer):
    categoria_nombre = serializers.CharField(source='categoria.nombre', read_only=True)

    class Meta:
        model = Producto
        fields = ['id', 'nombre', 'descripcion', 'precio', 'categoria', 'categoria_nombre', 'tipo_producto', 'imagen', 'disponible', 'vegetariano', 'vegano', 'gluten_free', 'picantes', 'tiempo_preparacion', 'alergenos', 'orden', 'fecha_creacion']