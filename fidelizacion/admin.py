from django.contrib import admin
from .models import Beneficio, Cupon


@admin.register(Beneficio)
class BeneficioAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'tipo', 'porcentaje', 'puntos_necesarios', 'producto_gratis', 'cantidad_producto', 'activo')
    list_filter = ('tipo', 'activo')
    search_fields = ('nombre', 'descripcion')
    list_editable = ('activo', 'porcentaje', 'puntos_necesarios', 'cantidad_producto')
    fieldsets = (
        ('Información del Beneficio', {
            'fields': ('nombre', 'descripcion', 'tipo')
        }),
        ('Configuración', {
            'fields': ('porcentaje', 'puntos_necesarios', 'activo')
        }),
        ('Producto Gratis', {
            'fields': ('producto_gratis', 'cantidad_producto'),
            'classes': ('collapse',)
        }),
        ('Fechas', {
            'fields': ('fecha_inicio', 'fecha_fin'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Cupon)
class CuponAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'descripcion', 'tipo', 'valor', 'valor_minimo', 'usos_actuales', 'usos_maximos', 'activo')
    list_filter = ('tipo', 'activo')
    search_fields = ('codigo', 'descripcion')
    list_editable = ('activo',)
    readonly_fields = ('usos_actuales', 'fecha_creacion')
    fieldsets = (
        ('Información del Cupón', {
            'fields': ('codigo', 'descripcion', 'tipo', 'valor', 'valor_minimo')
        }),
        ('Límites de Uso', {
            'fields': ('usos_maximos', 'usos_actuales')
        }),
        ('Fechas', {
            'fields': ('fecha_creacion', 'fecha_inicio', 'fecha_fin', 'activo')
        }),
    )
