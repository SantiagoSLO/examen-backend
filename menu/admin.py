from django.contrib import admin
from .models import Categoria, Producto, Promocion, MenuDelDia


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'orden', 'activa', 'get_productos_count', 'fecha_creacion')
    list_filter = ('activa',)
    search_fields = ('nombre', 'descripcion')
    ordering = ('orden', 'nombre')
    list_editable = ('orden', 'activa')
    fieldsets = (
        ('Información', {
            'fields': ('nombre', 'descripcion', 'imagen')
        }),
        ('Configuración', {
            'fields': ('orden', 'activa')
        }),
    )


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'categoria', 'precio', 'tipo_producto', 'disponible', 'vegetariano', 'vegano', 'orden')
    list_filter = ('categoria', 'tipo_producto', 'disponible', 'vegetariano', 'vegano', 'gluten_free')
    search_fields = ('nombre', 'descripcion', 'alergenos')
    ordering = ('categoria', 'orden', 'nombre')
    list_editable = ('disponible', 'orden', 'precio')
    fieldsets = (
        ('Información Básica', {
            'fields': ('nombre', 'descripcion', 'precio', 'categoria', 'tipo_producto')
        }),
        ('Imagen', {
            'fields': ('imagen',)
        }),
        ('Disponibilidad', {
            'fields': ('disponible', 'tiempo_preparacion')
        }),
        ('Características', {
            'fields': ('vegetariano', 'vegano', 'gluten_free', 'picantes', 'alergenos')
        }),
        ('Organización', {
            'fields': ('orden',),
            'classes': ('collapse',)
        }),
    )


@admin.register(Promocion)
class PromocionAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'porcentaje', 'fecha_inicio', 'fecha_fin', 'activa')
    list_filter = ('activa',)
    search_fields = ('titulo', 'descripcion', 'codigo')
    filter_horizontal = ('productos',)
    list_editable = ('activa',)
    fieldsets = (
        ('Información', {
            'fields': ('titulo', 'descripcion', 'codigo', 'porcentaje')
        }),
        ('Productos en Promoción', {
            'fields': ('productos',)
        }),
        ('Fechas', {
            'fields': ('fecha_inicio', 'fecha_fin', 'activa')
        }),
        ('Imagen', {
            'fields': ('imagen',),
            'classes': ('collapse',)
        }),
    )


@admin.register(MenuDelDia)
class MenuDelDiaAdmin(admin.ModelAdmin):
    list_display = ('fecha', 'entrada', 'plato_principal', 'bebida', 'precio_especial', 'disponible')
    list_filter = ('disponible', 'fecha')
    search_fields = ('fecha', 'notas')
    date_hierarchy = 'fecha'
    list_editable = ('disponible',)
    fieldsets = (
        ('Información', {
            'fields': ('fecha', 'entrada', 'plato_principal', 'bebida', 'postre', 'precio_especial', 'disponible')
        }),
        ('Notas', {
            'fields': ('notas',),
            'classes': ('collapse',)
        }),
    )
