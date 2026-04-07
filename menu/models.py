from django.db import models


class Categoria(models.Model):
    """Categorías del menú del restaurante"""
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    orden = models.IntegerField(default=0)
    activa = models.BooleanField(default=True)
    imagen = models.ImageField(upload_to='categorias/', blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías'
        ordering = ['orden', 'nombre']
    
    def __str__(self):
        return self.nombre
    
    def get_productos_count(self):
        return self.productos.filter(disponible=True).count()


class Producto(models.Model):
    """Productos del menú"""
    
    TIPO_PRODUCTO = [
        ('B', 'Bebida'),
        ('A', 'Acompañamiento'),
        ('P', 'Plato Principal'),
        ('D', 'Postre'),
        ('O', 'Otro'),
    ]
    
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField()
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT, related_name='productos')
    tipo_producto = models.CharField(max_length=1, choices=TIPO_PRODUCTO, default='P')
    imagen = models.ImageField(upload_to='productos/', blank=True, null=True)
    disponible = models.BooleanField(default=True)
    vegetariano = models.BooleanField(default=False)
    vegano = models.BooleanField(default=False)
    gluten_free = models.BooleanField(default=False)
    picantes = models.IntegerField(default=0)  # 0-5 nivel de picante
    tiempo_preparacion = models.IntegerField(default=15)  # en minutos
    alergenos = models.TextField(blank=True, help_text="Lista de alérgenos separados por coma")
    orden = models.IntegerField(default=0)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'
        ordering = ['orden', 'nombre']
    
    def __str__(self):
        return f"{self.nombre} - ${self.precio}"
    
    def get_precio_con_descuento(self):
        """Retorna el precio con descuento si hay promoción activa"""
        promocion = self.promociones.filter(activa=True).first()
        if promocion:
            return self.precio * (1 - promocion.porcentaje / 100)
        return self.precio


class Promocion(models.Model):
    """Promociones especiales del restaurante"""
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField()
    productos = models.ManyToManyField(Producto, related_name='promociones')
    porcentaje = models.DecimalField(max_digits=5, decimal_places=2, help_text="Porcentaje de descuento")
    fecha_inicio = models.DateTimeField()
    fecha_fin = models.DateTimeField()
    activa = models.BooleanField(default=True)
    imagen = models.ImageField(upload_to='promociones/', blank=True, null=True)
    codigo = models.CharField(max_length=20, unique=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Promoción'
        verbose_name_plural = 'Promociones'
        ordering = ['-fecha_inicio']
    
    def __str__(self):
        return f"{self.titulo} ({self.porcentaje}% desc)"
    
    def esta_activa(self):
        from django.utils import timezone
        return self.activa and self.fecha_inicio <= timezone.now() <= self.fecha_fin


class MenuDelDia(models.Model):
    """Menú del día"""
    fecha = models.DateField(unique=True)
    entrada = models.ForeignKey(Producto, on_delete=models.PROTECT, related_name='menu_entrada', limit_choices_to={'tipo_producto__in': ['A', 'O']})
    plato_principal = models.ForeignKey(Producto, on_delete=models.PROTECT, related_name='menu_principal', limit_choices_to={'tipo_producto': 'P'})
    bebida = models.ForeignKey(Producto, on_delete=models.PROTECT, related_name='menu_bebida', limit_choices_to={'tipo_producto': 'B'})
    postre = models.ForeignKey(Producto, on_delete=models.PROTECT, related_name='menu_postre', limit_choices_to={'tipo_producto': 'D'})
    precio_especial = models.DecimalField(max_digits=10, decimal_places=2)
    disponible = models.BooleanField(default=True)
    notas = models.TextField(blank=True)
    
    class Meta:
        verbose_name = 'Menú del Día'
        verbose_name_plural = 'Menús del Día'
        ordering = ['-fecha']
    
    def __str__(self):
        return f"Menú del {self.fecha}"
