from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class Perfil(models.Model):
    """Modelo extendido de usuario para el restaurante"""
    
    TIPO_DOCUMENTO = [
        ('CC', 'Cédula de Ciudadanía'),
        ('CE', 'Cédula de Extranjería'),
        ('TI', 'Tarjeta de Identidad'),
        ('RC', 'Registro Civil'),
        ('NIT', 'NIT'),
    ]
    
    TIPO_CLIENTE = [
        ('F', 'Frecuente'),
        ('O', 'Ocasional'),
        ('VIP', 'VIP - Cliente Premium'),
    ]
    
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    telefono = models.CharField(max_length=20, blank=True)
    tipo_documento = models.CharField(max_length=3, choices=TIPO_DOCUMENTO, default='CC')
    numero_documento = models.CharField(max_length=20, unique=True, blank=True, null=True)
    direccion = models.TextField(blank=True)
    fecha_nacimiento = models.DateField(null=True, blank=True)
    tipo_cliente = models.CharField(max_length=3, choices=TIPO_CLIENTE, default='O')
    puntos_fidelidad = models.IntegerField(default=0)
    nivel_fidelidad = models.IntegerField(default=1)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    ultimo_pedido = models.DateTimeField(null=True, blank=True)
    total_pedidos = models.IntegerField(default=0)
    gasto_total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    activo = models.BooleanField(default=True)
    notas = models.TextField(blank=True)
    cupones_usados = models.JSONField(default=list, blank=True, help_text="Lista de códigos de cupones ya utilizados")
    direccion_latitud = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, help_text="Latitud de la dirección guardada")
    direccion_longitud = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, help_text="Longitud de la dirección guardada")
    
    class Meta:
        verbose_name = 'Perfil de Usuario'
        verbose_name_plural = 'Perfiles de Usuarios'
        ordering = ['-fecha_registro']
    
    def __str__(self):
        return f"{self.usuario.get_full_name() or self.usuario.username} - {self.get_tipo_cliente_display()}"
    
    def calcular_nivel(self):
        """Calcula el nivel de fidelización basado en número de pedidos"""
        # Niveles basados en cantidad de pedidos
        if self.total_pedidos >= 15:
            self.nivel_fidelidad = 3  # VIP
            self.tipo_cliente = 'VIP'
        elif self.total_pedidos >= 10:
            self.nivel_fidelidad = 2  # Frecuente
            self.tipo_cliente = 'F'
        elif self.total_pedidos >= 5:
            self.nivel_fidelidad = 1  # Ocasional
            self.tipo_cliente = 'O'
        else:
            self.nivel_fidelidad = 1  # Ocasional
            self.tipo_cliente = 'O'
        self.save()
    
    def agregar_puntos(self, puntos):
        """Agrega puntos de fidelidad y recalcula nivel"""
        self.puntos_fidelidad += puntos
        self.calcular_nivel()
    
    def get_beneficios_activos(self):
        """Retorna los beneficios disponibles para el cliente según su nivel"""
        from fidelizacion.models import Beneficio
        return Beneficio.objects.filter(
            nivel_minimo__lte=self.nivel_fidelidad,
            activo=True
        )


@receiver(post_save, sender=User)
def crear_perfil_usuario(sender, instance, created, **kwargs):
    """Signal para crear perfil automáticamente cuando se crea un usuario"""
    if created:
        Perfil.objects.create(usuario=instance)


@receiver(post_save, sender=User)
def guardar_perfil_usuario(sender, instance, **kwargs):
    """Signal para guardar perfil cuando se guarda el usuario"""
    try:
        instance.perfil.save()
    except Perfil.DoesNotExist:
        Perfil.objects.create(usuario=instance)
