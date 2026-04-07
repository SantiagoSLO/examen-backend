"""
Script para crear los beneficios iniciales del programa de fidelización
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'restaurante.settings')
django.setup()

from fidelizacion.models import Beneficio
from menu.models import Producto, Categoria

def crear_beneficios():
    """Crea los beneficios iniciales del programa de fidelización"""
    
    # Buscar productos para regalar
    try:
        categoria_entrada = Categoria.objects.get(nombre__icontains='entrada')
        entrada = Producto.objects.filter(categoria=categoria_entrada, disponible=True).first()
    except:
        entrada = None
    
    try:
        categoria_bebida = Categoria.objects.get(nombre__icontains='bebida')
        bebida = Producto.objects.filter(categoria=categoria_bebida, disponible=True).first()
    except:
        bebida = None
    
    try:
        categoria_principal = Categoria.objects.get(nombre__icontains='principal')
        principal = Producto.objects.filter(categoria=categoria_principal, disponible=True).first()
    except:
        principal = None
    
    beneficios = [
        # Descuentos
        {
            'nombre': '5% de Descuento',
            'descripcion': 'Obtén un 5% de descuento en tu próximo pedido',
            'tipo': 'D',
            'porcentaje': 5,
            'puntos_necesarios': 99,
            'activo': True,
        },
        {
            'nombre': '10% de Descuento',
            'descripcion': 'Obtén un 10% de descuento en tu próximo pedido',
            'tipo': 'D',
            'porcentaje': 10,
            'puntos_necesarios': 500,
            'activo': True,
        },
        {
            'nombre': '15% de Descuento',
            'descripcion': 'Obtén un 15% de descuento en tu próximo pedido',
            'tipo': 'D',
            'porcentaje': 15,
            'puntos_necesarios': 700,
            'activo': True,
        },
        {
            'nombre': '20% de Descuento',
            'descripcion': 'Obtén un 20% de descuento en tu próximo pedido',
            'tipo': 'D',
            'porcentaje': 20,
            'puntos_necesarios': 900,
            'activo': True,
        },
        # Productos gratis
        {
            'nombre': 'Entrada Gratis',
            'descripcion': 'Recibe una entrada gratis (empanadas)',
            'tipo': 'P',
            'porcentaje': 100,
            'puntos_necesarios': 450,
            'producto_gratis': entrada,
            'cantidad_producto': 1,
            'activo': True,
        },
        {
            'nombre': '2 Entradas Gratis',
            'descripcion': 'Recibe 2 entradas gratis (empanadas)',
            'tipo': 'P',
            'porcentaje': 100,
            'puntos_necesarios': 800,
            'producto_gratis': entrada,
            'cantidad_producto': 2,
            'activo': True,
        },
        {
            'nombre': 'Bebida Gratis',
            'descripcion': 'Recibe una bebida gratis',
            'tipo': 'P',
            'porcentaje': 100,
            'puntos_necesarios': 300,
            'producto_gratis': bebida,
            'cantidad_producto': 1,
            'activo': True,
        },
        {
            'nombre': 'Postre Gratis',
            'descripcion': 'Recibe un postre gratis',
            'tipo': 'P',
            'porcentaje': 100,
            'puntos_necesarios': 550,
            'producto_gratis': principal,  # Usamos cualquier producto disponible
            'cantidad_producto': 1,
            'activo': True,
        },
    ]
    
    # Crear o actualizar beneficios
    for beneficio_data in beneficios:
        # Extraer producto_gratis y cantidad_producto si existen
        producto_gratis = beneficio_data.pop('producto_gratis', None)
        cantidad_producto = beneficio_data.pop('cantidad_producto', 1)
        
        beneficio, created = Beneficio.objects.update_or_create(
            nombre=beneficio_data['nombre'],
            defaults=beneficio_data
        )
        
        if producto_gratis:
            beneficio.producto_gratis = producto_gratis
            beneficio.cantidad_producto = cantidad_producto
            beneficio.save()
        
        if created:
            print(f"[OK] Beneficio creado: {beneficio.nombre} ({beneficio.puntos_necesarios} puntos)")
        else:
            print(f"[OK] Beneficio actualizado: {beneficio.nombre}")
    
    print(f"\n✓ Se crearon {len(beneficios)} beneficios")
    print("Ahora los clientes pueden canjear estos beneficios con sus puntos!")

if __name__ == '__main__':
    crear_beneficios()
