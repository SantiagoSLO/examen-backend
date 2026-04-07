from django.contrib import admin
from .models import Pedido, ItemPedido, Carrito


class ItemPedidoInline(admin.TabularInline):
    model = ItemPedido
    extra = 0
    fields = ('producto', 'cantidad', 'precio_unitario', 'subtotal', 'notas')
    readonly_fields = ('producto', 'cantidad', 'precio_unitario', 'subtotal')
    can_delete = True
    max_num = 0


@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ('numero_pedido', 'cliente', 'tipo_pedido', 'estado', 'subtotal', 'descuento', 'descuento_puntos', 'total', 'puntos_ganados', 'puntos_canjeados', 'fecha_pedido')
    list_filter = ('estado', 'tipo_pedido', 'metodo_pago', 'fecha_pedido')
    search_fields = ('numero_pedido', 'cliente__username', 'cliente__email', 'cliente__first_name', 'cliente__last_name')
    readonly_fields = ('numero_pedido', 'fecha_pedido', 'subtotal', 'puntos_ganados')
    list_editable = ('estado',)
    inlines = [ItemPedidoInline]
    date_hierarchy = 'fecha_pedido'
    actions = ['confirmar_pedidos', 'cancelar_pedidos', 'marcar_finalizados', 'marcar_en_preparacion', 'marcar_listo']
    
    fieldsets = (
        ('Información del Pedido', {
            'fields': ('numero_pedido', 'cliente', 'tipo_pedido', 'estado', 'metodo_pago')
        }),
        ('Fechas', {
            'fields': ('fecha_pedido', 'fecha_confirmacion', 'fecha_entrega'),
            'classes': ('collapse',)
        }),
        ('Entrega', {
            'fields': ('direccion_entrega', 'telefono_contacto', 'notas_entrega')
        }),
        ('Totales', {
            'fields': ('subtotal', 'descuento', 'descuento_puntos', 'costo_domicilio', 'total')
        }),
        ('Puntos de Fidelización', {
            'fields': ('puntos_ganados', 'puntos_canjeados'),
            'classes': ('collapse',)
        }),
        ('Notas', {
            'fields': ('notas',)
        }),
    )
    
    def confirmar_pedidos(self, request, queryset):
        for pedido in queryset.filter(estado='P'):
            pedido.estado = 'C'
            pedido.save()
        self.message_user(request, f"{queryset.filter(estado='P').count()} pedidos confirmados.")
    confirmar_pedidos.short_description = "Confirmar pedidos seleccionados"
    
    def cancelar_pedidos(self, request, queryset):
        queryset.update(estado='X')
        self.message_user(request, f"{queryset.count()} pedidos cancelados.")
    cancelar_pedidos.short_description = "Cancelar pedidos seleccionados"
    
    def marcar_finalizados(self, request, queryset):
        queryset.update(estado='F')
        self.message_user(request, f"{queryset.count()} pedidos marcados como finalizados.")
    marcar_finalizados.short_description = "Finalizar pedidos seleccionados"
    
    def marcar_en_preparacion(self, request, queryset):
        queryset.update(estado='E')
        self.message_user(request, f"{queryset.count()} pedidos marcados en preparación.")
    marcar_en_preparacion.short_description = "Marcar en preparación"
    
    def marcar_listo(self, request, queryset):
        queryset.update(estado='R')
        self.message_user(request, f"{queryset.count()} pedidos marcados como listos.")
    marcar_listo.short_description = "Marcar como listos para recoger"


@admin.register(Carrito)
class CarritoAdmin(admin.ModelAdmin):
    list_display = ('session_key', 'usuario', 'producto', 'cantidad', 'fecha_creacion')
    list_filter = ('fecha_creacion',)
    search_fields = ('session_key', 'usuario__username', 'producto__nombre')
    readonly_fields = ('session_key', 'usuario', 'producto', 'cantidad', 'fecha_creacion')
