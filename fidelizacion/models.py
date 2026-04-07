from django.db import models
from django.conf import settings
from menu.models import Producto


class Beneficio(models.Model):
    """Beneficios de fidelizacion para clientes"""
    
    TIPO_BENEFICIO = [
        ('D', 'Descuento'),
        ('P', 'Producto Gratis'),
        ('E', 'Evento Especial'),
        ('B', 'Bebida Gratis'),
        ('E', 'Entrada Gratis'),
    ]
    
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField()
    tipo = models.CharField(max_length=1, choices=TIPO_BENEFICIO, default='D')
    porcentaje = models.DecimalField(max_digits=5, decimal_places=2, default=0, help_text="Porcentaje de descuento")
    nivel_minimo = models.IntegerField(default=1, help_text="Nivel minimo requerido")
    puntos_necesarios = models.IntegerField(default=0, help_text="Puntos necesarios para canjear")
    # Producto gratis (para tipo 'P' = Producto Gratis, 'B' = Bebida, 'E' = Entrada)
    producto_gratis = models.ForeignKey(
        Producto, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='beneficios_producto',
        help_text="Producto que se regalará (para productos/entradas/bebidas gratis)"
    )
    cantidad_producto = models.IntegerField(default=1, help_text="Cantidad del producto gratis")
    activo = models.BooleanField(default=True)
    fecha_inicio = models.DateField(null=True, blank=True)
    fecha_fin = models.DateField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'Beneficio'
        verbose_name_plural = 'Beneficios'
        ordering = ['puntos_necesarios']
    
    def __str__(self):
        return f"{self.nombre} ({self.puntos_necesarios} puntos)"
    
    def puede_canjear(self, perfil):
        """Verifica si el usuario puede canjear este beneficio"""
        if not self.activo:
            return False
        if perfil.puntos_fidelidad < self.puntos_necesarios:
            return False
        return True
    
    def canjear(self, perfil):
        """Canjea el beneficio para el perfil dado"""
        if not self.puede_canjear(perfil):
            return False
        
        perfil.puntos_fidelidad -= self.puntos_necesarios
        perfil.save()
        return True


class Cupon(models.Model):
    """Cupones de descuento"""
    
    TIPO_CUPON = [
        ('P', 'Porcentaje'),
        ('F', 'Fijo'),
    ]
    
    codigo = models.CharField(max_length=20, unique=True)
    descripcion = models.TextField()
    tipo = models.CharField(max_length=1, choices=TIPO_CUPON, default='P')
    valor = models.DecimalField(max_digits=10, decimal_places=2, help_text="Porcentaje o valor fijo")
    valor_minimo = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Valor minimo de compra para aplicar")
    usos_maximos = models.IntegerField(default=1, help_text="Usos maximos del cupon")
    usos_actuales = models.IntegerField(default=0)
    activo = models.BooleanField(default=True)
    fecha_inicio = models.DateField(null=True, blank=True)
    fecha_fin = models.DateField(null=True, blank=True)
    creado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Cupon'
        verbose_name_plural = 'Cupones'
    
    def __str__(self):
        return f"{self.codigo} ({self.valor}{'%' if self.tipo == 'P' else '$'})"
    
    def aplicar_descuento(self, monto):
        """Aplica el descuento al monto dado"""
        if self.tipo == 'P':
            return monto * (self.valor / 100)
        else:
            return min(self.valor, monto)
    
    def esta_activo(self):
        """Verifica si el cupon esta activo"""
        from django.utils import timezone
        now = timezone.now().date()
        
        if not self.activo:
            return False
        
        if self.fecha_inicio and self.fecha_inicio > now:
            return False
        
        if self.fecha_fin and self.fecha_fin < now:
            return False
        
        if self.usos_maximos and self.usos_actuales >= self.usos_maximos:
            return False
        
        return True
