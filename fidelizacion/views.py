from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.db import models
from django.db.models import Sum
from .models import Beneficio, Cupon
from menu.models import Promocion
from usuarios.models import Perfil


def programa_fidelidad(request):
    """Vista publica del programa de fidelizacion"""
    beneficios = Beneficio.objects.filter(activo=True)
    promociones = Promocion.objects.filter(activa=True)
    # Obtener cupones activos disponibles
    from django.utils import timezone
    hoy = timezone.now().date()
    cupones = Cupon.objects.filter(activo=True).filter(
        models.Q(fecha_inicio__isnull=True) | models.Q(fecha_inicio__lte=hoy)
    ).filter(
        models.Q(fecha_fin__isnull=True) | models.Q(fecha_fin__gte=hoy)
    ).filter(
        models.Q(usos_maximos__isnull=True) | models.Q(usos_actuales__lt=models.F('usos_maximos'))
    )
    
    context = {
        'beneficios': beneficios,
        'promociones': promociones,
        'cupones': cupones
    }
    
    # Si el usuario esta autenticado, mostrar su informacion
    if request.user.is_authenticated:
        try:
            perfil = request.user.perfil
            context['perfil'] = perfil
            context['mis_beneficios'] = perfil.get_beneficios_activos()
            
            # Calcular beneficios por cantidad de pedidos
            total_pedidos = perfil.total_pedidos or 0
            
            # 5+ pedidos = proximo pedido gratis
            if total_pedidos >= 5:
                context['pedido_gratis'] = True
            
            # 10+ pedidos = entrada gratis (empanadas)
            if total_pedidos >= 10:
                context['entrada_gratis'] = True
                
            # 15+ pedidos = 2 entradas gratis
            if total_pedidos >= 15:
                context['dos_entradas_gratis'] = True
                
        except Perfil.DoesNotExist:
            pass
    
    return render(request, 'fidelizacion/programa.html', context)


@login_required
def aplicar_cupon(request):
    """Aplica un cupon de descuento"""
    if request.method == 'POST':
        codigo = request.POST.get('codigo', '').strip().upper()
        
        # Primero verificar si el usuario ya usó este cupón
        try:
            perfil = request.user.perfil
            cupones_usados = perfil.cupones_usados or []
            # Normalizar a mayúsculas para comparar
            cupones_usados_upper = [c.upper() for c in cupones_usados]
            if codigo in cupones_usados_upper:
                messages.error(request, f"El cupón '{codigo}' ya ha sido redimido anteriormente.")
                return redirect('carrito')
        except:
            pass  # Si no tiene perfil, continuar
        
        # Luego verificar si el cupón existe y está activo
        try:
            cupon = Cupon.objects.get(codigo__iexact=codigo)
            
            if not cupon.esta_activo():
                messages.error(request, "El cupon no esta activo o ha expirado.")
                return redirect('carrito')
            
            # Guardar el cupon en la sesion
            request.session['cupon_aplicado'] = {
                'codigo': cupon.codigo.upper(),  # Guardar en mayúsculas
                'tipo': cupon.tipo,
                'valor': str(cupon.valor),
                'valor_minimo': str(cupon.valor_minimo)
            }
            
            messages.success(request, f"Cupon '{cupon.codigo}' aplicado correctamente!")
            
        except Cupon.DoesNotExist:
            messages.error(request, "El cupon no existe.")
    
    return redirect('carrito')


def estadisticas_fidelizacion(request):
    """Estadisticas del programa de fidelizacion (para admin)"""
    if not request.user.is_staff:
        return redirect('inicio')
    
    from django.db.models import Count, Sum
    
    # Estadisticas generales
    total_clientes = Perfil.objects.count()
    clientes_activos = Perfil.objects.filter(total_pedidos__gt=0).count()
    
    # Distribucion por nivel
    niveles_distribucion = Perfil.objects.values('nivel_fidelidad').annotate(
        count=Count('id')
    ).order_by('nivel_fidelidad')
    
    # Puntos totales en el sistema
    puntos_totales = Perfil.objects.aggregate(Sum('puntos_fidelidad'))['puntos_fidelidad__sum'] or 0
    
    # Clientes con mas pedidos
    mejores_clientes = Perfil.objects.filter(total_pedidos__gt=0).order_by('-total_pedidos')[:10]
    
    context = {
        'total_clientes': total_clientes,
        'clientes_activos': clientes_activos,
        'niveles_distribucion': niveles_distribucion,
        'puntos_totales': puntos_totales,
        'mejores_clientes': mejores_clientes,
    }
    
    return render(request, 'fidelizacion/estadisticas.html', context)


@login_required
@require_POST
def canjear_beneficio(request, beneficio_id):
    """Canjea un beneficio y lo agrega al carrito"""
    beneficio = get_object_or_404(Beneficio, id=beneficio_id, activo=True)
    
    try:
        perfil = request.user.perfil
    except Perfil.DoesNotExist:
        messages.error(request, "No tienes un perfil de usuario.")
        return redirect('programa_fidelidad')
    
    # Verificar si el usuario tiene suficientes puntos
    if perfil.puntos_fidelidad < beneficio.puntos_necesarios:
        messages.error(request, f"No tienes suficientes puntos. Tienes {perfil.puntos_fidelidad} puntos y necesitas {beneficio.puntos_necesarios} puntos.")
        return redirect('programa_fidelidad')
    
    # Restar los puntos
    perfil.puntos_fidelidad -= beneficio.puntos_necesarios
    perfil.save()
    
    # Guardar el beneficio en la sesion del carrito
    beneficio_data = {
        'id': beneficio.id,
        'nombre': beneficio.nombre,
        'descripcion': beneficio.descripcion,
        'tipo': beneficio.tipo,
        'porcentaje': float(beneficio.porcentaje) if beneficio.porcentaje else 0,
        'puntos_utilizados': beneficio.puntos_necesarios,
        'producto_gratis_id': beneficio.producto_gratis.id if beneficio.producto_gratis else None,
        'cantidad_producto': beneficio.cantidad_producto,
    }
    
    # Obtener beneficios actuales en el carrito
    beneficios_carrito = request.session.get('beneficios_canjeados', [])
    beneficios_carrito.append(beneficio_data)
    request.session['beneficios_canjeados'] = beneficios_carrito
    
    messages.success(request, f"Has canjeado '{beneficio.nombre}' por {beneficio.puntos_necesarios} puntos!")
    
    return redirect('carrito')
