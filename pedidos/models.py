from django.db import models
from django.conf import settings
from menu.models import Producto


class Pedido(models.Model):
    """Modelo de pedido del restaurante"""
    
    TIPO_PEDIDO = [
        ('S', 'En el Restaurante'),
        ('D', 'Domicilio'),
    ]
    
    ESTADO_PEDIDO = [
        ('P', 'Pendiente'),
        ('C', 'Confirmado'),
        ('E', 'En Preparación'),
        ('E', 'Enviado'),  # Solo para domicilios
        ('R', 'Listo para Recoger'),
        ('F', 'Finalizado'),
        ('X', 'Cancelado'),
    ]
    
    METODO_PAGO = [
        ('EF', 'Efectivo'),
        ('TC', 'Tarjeta de Crédito/Débito'),
        ('NE', 'Nequi'),
        ('DA', 'Daviplata'),
        ('TR', 'Transferencia'),
    ]
    
    cliente = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='pedidos'
    )
    numero_pedido = models.CharField(max_length=20, unique=True)
    tipo_pedido = models.CharField(max_length=1, choices=TIPO_PEDIDO, default='S')
    estado = models.CharField(max_length=1, choices=ESTADO_PEDIDO, default='P')
    metodo_pago = models.CharField(max_length=2, choices=METODO_PAGO, default='EF')
    
    # Datos de entrega
    direccion_entrega = models.TextField(blank=True)
    telefono_contacto = models.CharField(max_length=20, blank=True)
    notas_entrega = models.TextField(blank=True)
    latitud = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, help_text="Latitud de la ubicación de entrega")
    longitud = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, help_text="Longitud de la ubicación de entrega")
    
    # Fechas
    fecha_pedido = models.DateTimeField(auto_now_add=True)
    fecha_confirmacion = models.DateTimeField(null=True, blank=True)
    fecha_entrega = models.DateTimeField(null=True, blank=True)
    
    # Totales
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    descuento = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    costo_domicilio = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Puntos de fidelidad
    puntos_ganados = models.IntegerField(default=0)
    puntos_canjeados = models.IntegerField(default=0)
    descuento_puntos = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Notas adicionales
    notas = models.TextField(blank=True)
    
    class Meta:
        verbose_name = 'Pedido'
        verbose_name_plural = 'Pedidos'
        ordering = ['-fecha_pedido']
    
    def __str__(self):
        return f"Pedido #{self.numero_pedido} - {self.cliente.username}"
    
    def save(self, *args, **kwargs):
        if not self.numero_pedido:
            from datetime import datetime
            fecha = datetime.now().strftime('%Y%m%d')
            ultimo = Pedido.objects.filter(numero_pedido__startswith=f"PED-{fecha}").count()
            self.numero_pedido = f"PED-{fecha}-{ultimo + 1:04d}"
        
        # Calcular total
        from decimal import Decimal
        self.total = self.subtotal - self.descuento - Decimal(str(self.descuento_puntos)) + self.costo_domicilio
        super().save(*args, **kwargs)
    
    def calcular_total(self):
        """Calcula el total del pedido"""
        from decimal import Decimal
        self.subtotal = sum(item.subtotal for item in self.items.all())
        self.total = self.subtotal - self.descuento - Decimal(str(self.descuento_puntos)) + self.costo_domicilio
        self.save()
    
    def confirmar_pedido(self):
        """Confirma el pedido y asigna puntos"""
        from django.utils import timezone
        self.estado = 'C'
        self.fecha_confirmacion = timezone.now()
        
        # Calcular puntos de fidelidad (1 punto por cada $1000)
        puntos = int(self.total)
        self.puntos_ganados = puntos
        
        # Agregar puntos al cliente
        perfil = self.cliente.perfil
        perfil.agregar_puntos(puntos)
        perfil.total_pedidos += 1
        perfil.ultimo_pedido = timezone.now()
        perfil.gasto_total += self.total
        perfil.save()
        
        self.save()
        return self.puntos_ganados
    
    def aplicar_descuento(self, porcentaje):
        """Aplica un descuento al pedido"""
        self.descuento = self.subtotal * (porcentaje / 100)
        self.save()


class ItemPedido(models.Model):
    """Items de un pedido"""
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='items')
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)
    cantidad = models.IntegerField(default=1)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    notas = models.TextField(blank=True)
    
    class Meta:
        verbose_name = 'Item de Pedido'
        verbose_name_plural = 'Items de Pedido'
    
    def __str__(self):
        return f"{self.cantidad}x {self.producto.nombre}"
    
    def save(self, *args, **kwargs):
        # Verificar si hay promoción activa para el producto
        self.precio_unitario = self.producto.get_precio_con_descuento()
        self.subtotal = self.precio_unitario * self.cantidad
        super().save(*args, **kwargs)


class Carrito(models.Model):
    """Carrito de compras temporal"""
    session_key = models.CharField(max_length=40, blank=True, null=True)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='carritos'
    )
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.IntegerField(default=1)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Carrito'
        verbose_name_plural = 'Carritos'
    
    def __str__(self):
        return f"{self.cantidad}x {self.producto.nombre}"
    
    @property
    def subtotal(self):
        return self.producto.get_precio_con_descuento() * self.cantidad
