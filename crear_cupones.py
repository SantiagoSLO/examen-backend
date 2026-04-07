#!/usr/bin/env python
"""Script para crear cupones de descuento"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'restaurante.settings')
django.setup()

from fidelizacion.models import Cupon
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

User = get_user_model()
admin_user = User.objects.filter(is_superuser=True).first()

if not admin_user:
    print("No hay superuser. Creando...")
    admin_user = User.objects.create_superuser('admin', 'admin@test.com', 'admin123')

# Crear cupones de prueba
cupones_data = [
    {'codigo': 'BIENVENIDO10', 'descripcion': '10% de descuento en tu primer pedido', 'tipo': 'P', 'valor': 10, 'valor_minimo': 20000, 'usos_maximos': 100},
    {'codigo': 'SABOR20', 'descripcion': '20% de descuento en pedidos mayores a $50,000', 'tipo': 'P', 'valor': 20, 'valor_minimo': 50000, 'usos_maximos': 50},
    {'codigo': 'FIEL5000', 'descripcion': '$5,000 de descuento fijo', 'tipo': 'F', 'valor': 5000, 'valor_minimo': 30000, 'usos_maximos': 30},
]

for data in cupones_data:
    cupon, created = Cupon.objects.get_or_create(
        codigo=data['codigo'],
        defaults={
            'descripcion': data['descripcion'],
            'tipo': data['tipo'],
            'valor': data['valor'],
            'valor_minimo': data.get('valor_minimo', 0),
            'usos_maximos': data.get('usos_maximos', 1),
            'activo': True,
            'creado_por': admin_user,
            'fecha_inicio': timezone.now().date(),
            'fecha_fin': timezone.now().date() + timedelta(days=30)
        }
    )
    if created:
        print(f'Cupón {cupon.codigo} creado')
    else:
        print(f'Cupón {cupon.codigo} ya existe')

print(f'Total de cupones: {Cupon.objects.count()}')
