from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Perfil


class PerfilInline(admin.StackedInline):
    model = Perfil
    can_delete = False
    verbose_name_plural = 'Perfil'
    fieldsets = (
        ('Información Personal', {
            'fields': ('telefono', 'tipo_documento', 'numero_documento', 'direccion', 'fecha_nacimiento')
        }),
        ('Información de Cliente', {
            'fields': ('tipo_cliente', 'puntos_fidelidad', 'nivel_fidelidad', 'total_pedidos', 'gasto_total')
        }),
        ('Estado', {
            'fields': ('activo', 'notas')
        }),
        ('Fechas', {
            'fields': ('fecha_registro', 'ultimo_pedido'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('fecha_registro', 'ultimo_pedido', 'puntos_fidelidad', 'nivel_fidelidad', 'total_pedidos', 'gasto_total')


class UserAdmin(BaseUserAdmin):
    inlines = (PerfilInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'get_tipo_cliente', 'get_puntos', 'get_pedidos')
    list_filter = ('is_staff', 'is_superuser', 'perfil__tipo_cliente', 'perfil__activo')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'perfil__numero_documento')
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('username', 'password', 'email', 'first_name', 'last_name')
        }),
        ('Permisos', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'classes': ('collapse',)
        }),
        ('Fechas Importantes', {
            'fields': ('last_login', 'date_joined'),
            'classes': ('collapse',)
        }),
    )
    
    def get_tipo_cliente(self, obj):
        return obj.perfil.get_tipo_cliente_display()
    get_tipo_cliente.short_description = 'Tipo de Cliente'
    
    def get_puntos(self, obj):
        return obj.perfil.puntos_fidelidad
    get_puntos.short_description = 'Puntos'
    
    def get_pedidos(self, obj):
        return obj.perfil.total_pedidos
    get_pedidos.short_description = 'Pedidos'


# Registrar el modelo User con la configuración personalizada
admin.site.unregister(User)
admin.site.register(User, UserAdmin)

# Registrar el modelo Perfil separately if needed
@admin.register(Perfil)
class PerfilAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'telefono', 'tipo_cliente', 'puntos_fidelidad', 'nivel_fidelidad', 'total_pedidos', 'gasto_total', 'activo')
    list_filter = ('tipo_cliente', 'nivel_fidelidad', 'activo')
    search_fields = ('usuario__username', 'usuario__email', 'usuario__first_name', 'usuario__last_name', 'numero_documento')
    readonly_fields = ('fecha_registro', 'ultimo_pedido')
    list_editable = ('activo',)
    ordering = ('-total_pedidos', '-gasto_total')
    list_per_page = 25
    fieldsets = (
        ('Usuario', {
            'fields': ('usuario',)
        }),
        ('Información Personal', {
            'fields': ('telefono', 'tipo_documento', 'numero_documento', 'direccion', 'fecha_nacimiento')
        }),
        ('Estado de Fidelización', {
            'fields': ('tipo_cliente', 'puntos_fidelidad', 'nivel_fidelidad', 'total_pedidos', 'gasto_total')
        }),
        ('Información Adicional', {
            'fields': ('activo', 'notas', 'fecha_registro', 'ultimo_pedido'),
            'classes': ('collapse',)
        }),
    )
