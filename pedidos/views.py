from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.http import JsonResponse, HttpResponse
from django.db.models import Sum, Count
from decimal import Decimal
from .models import Pedido, ItemPedido
from menu.models import Producto, MenuDelDia
from fidelizacion.models import Cupon, Beneficio
from usuarios.models import Perfil
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from io import BytesIO
from django.utils import timezone
from datetime import date, datetime


def ver_carrito(request):
    """Vista del carrito de compras"""
    # Obtener items del carrito desde la sesión
    carrito = request.session.get('carrito', [])
    
    # Calcular subtotal
    subtotal = Decimal('0')
    items = []
    
    for item in carrito:
        producto = Producto.objects.get(id=item['producto_id'])
        cantidad = int(item['cantidad'])
        precio = producto.get_precio_con_descuento()
        items.append({
            'id': item['id'],
            'producto': producto,
            'cantidad': cantidad,
            'precio': precio,
            'subtotal': precio * cantidad
        })
        subtotal += precio * cantidad
    
    # Descuentes
    descuento = 0
    descuento_cupon = 0
    descuento_puntos = 0
    descuento_beneficios = 0
    descuento_menu_dia = Decimal(str(request.session.get('descuento_menu_dia', 0)))
    
    # Calcular descuento por beneficios canjeados
    descuento_beneficios = 0
    beneficios_session = request.session.get('beneficios_canjeados', [])
    if beneficios_session:
        for benef in beneficios_session:
            # Si es un descuento (tipo D) o tiene porcentaje mayor a 0, aplicarlo
            if benef['tipo'] == 'D' or (benef['tipo'] == 'P' and benef['porcentaje'] > 0):
                descuento_beneficios += subtotal * (Decimal(str(benef['porcentaje'])) / 100)
    
    # Aplicar cupón si hay
    cupon_data = request.session.get('cupon_aplicado')
    if cupon_data:
        try:
            cupon = Cupon.objects.get(codigo=cupon_data['codigo'])
            if cupon.esta_activo() and (cupon.valor_minimo is None or subtotal >= cupon.valor_minimo):
                descuento_cupon = cupon.aplicar_descuento(subtotal)
            else:
                request.session.pop('cupon_aplicado', None)
        except Cupon.DoesNotExist:
            pass
    
    # Calcular descuento por puntos
    puntos_data = request.session.get('puntos_aplicados')
    if puntos_data:
        descuento_puntos = puntos_data['descuento']
    
    # Calcular total
    total = subtotal - descuento - descuento_cupon - Decimal(str(descuento_puntos)) - Decimal(str(descuento_beneficios)) - descuento_menu_dia
    
    # Puntos disponibles del usuario
    puntos_disponibles = 0
    perfil_data = None
    if request.user.is_authenticated:
        try:
            perfil = request.user.perfil
            puntos_disponibles = perfil.puntos_fidelidad
            perfil_data = perfil
        except Perfil.DoesNotExist:
            pass
    
    context = {
        'items': items,
        'subtotal': subtotal,
        'descuento': descuento,
        'descuento_cupon': descuento_cupon,
        'descuento_puntos': descuento_puntos,
        'descuento_beneficios': descuento_beneficios,
        'descuento_menu_dia': descuento_menu_dia,
        'total': total,
        'puntos_disponibles': puntos_disponibles,
        'cupon_aplicado': cupon_data,
        'beneficios_canjeados': beneficios_session,
        'perfil': perfil_data,
    }
    
    return render(request, 'pedidos/carrito.html', context)


@require_POST
def agregar_al_carrito(request, producto_id):
    """Agrega un producto al carrito"""
    producto = get_object_or_404(Producto, id=producto_id, disponible=True)
    cantidad = int(request.POST.get('cantidad', 1))
    
    # Obtener o crear el carrito en la sesión
    carrito = request.session.get('carrito', [])
    
    # Verificar si el producto ya está en el carrito
    encontrado = False
    for item in carrito:
        if item['producto_id'] == producto_id:
            item['cantidad'] = int(item['cantidad']) + cantidad
            encontrado = True
            break
    
    if not encontrado:
        import uuid
        item_id = str(uuid.uuid4())[:8]
        carrito.append({
            'id': item_id,
            'producto_id': producto_id,
            'cantidad': cantidad
        })
    
    request.session['carrito'] = carrito
    messages.success(request, f"{producto.nombre} agregado al carrito")
    return redirect('carrito')


@require_POST
def actualizar_carrito(request, item_id):
    """Actualiza la cantidad de un producto en el carrito"""
    cantidad = int(request.POST.get('cantidad', 1))
    
    carrito = request.session.get('carrito', [])
    
    for item in carrito:
        if item['id'] == item_id:
            if cantidad > 0:
                item['cantidad'] = cantidad
            else:
                carrito.remove(item)
            break
    
    request.session['carrito'] = carrito
    return redirect('carrito')


@require_POST
def eliminar_del_carrito(request, item_id):
    """Elimina un producto del carrito"""
    # El item_id viene de la URL, no del POST
    
    carrito = request.session.get('carrito', [])
    carrito = [item for item in carrito if item['id'] != item_id]
    
    request.session['carrito'] = carrito
    messages.success(request, "Producto eliminado del carrito")
    return redirect('carrito')


@require_POST
def aplicar_puntos(request):
    """Aplica puntos de fidelidad como descuento"""
    if not request.user.is_authenticated:
        messages.error(request, "Debes iniciar sesión para usar tus puntos")
        return redirect('login')
    
    puntos = int(request.POST.get('puntos', 0))
    
    try:
        perfil = request.user.perfil
    except Perfil.DoesNotExist:
        messages.error(request, "No tienes un perfil de usuario")
        return redirect('carrito')
    
    if puntos > perfil.puntos_fidelidad:
        messages.error(request, "No tienes suficientes puntos")
        return redirect('carrito')
    
    # 100 puntos = $1,000 de descuento
    descuento = (Decimal(puntos) / 100) * Decimal('1000')
    
    request.session['puntos_aplicados'] = {
        'puntos': puntos,
        'descuento': float(descuento)
    }
    
    messages.success(request, f"{puntos} puntos aplicados. Descuento: ${descuento:,.0f}")
    return redirect('carrito')


@require_POST
def agregar_menu_dia(request):
    """Agrega el menú del día al carrito"""
    from decimal import Decimal
    
    menu_id = request.POST.get('menu_id')
    menu = get_object_or_404(MenuDelDia, id=menu_id, disponible=True)
    
    # Calcular descuento (precio especial vs precio normal)
    precio_normal = (
        menu.entrada.precio + 
        menu.plato_principal.precio + 
        menu.bebida.precio + 
        menu.postre.precio
    )
    precio_especial = menu.precio_especial
    
    # Solo agregar si hay un descuento real
    if precio_especial < precio_normal:
        descuento_menu = precio_normal - precio_especial
        # Guardar el descuento del menú en la sesión
        request.session['descuento_menu_dia'] = float(descuento_menu)
        
        # Agregar los productos individuales al carrito
        carrito = request.session.get('carrito', [])
        import uuid
        
        # Agregar cada producto del menú
        for producto, cantidad in [
            (menu.entrada, 1),
            (menu.plato_principal, 1),
            (menu.bebida, 1),
            (menu.postre, 1)
        ]:
            item_id = str(uuid.uuid4())[:8]
            carrito.append({
                'id': item_id,
                'producto_id': producto.id,
                'cantidad': cantidad,
                'es_menu_dia': True,
                'menu_id': menu.id
            })
        
        request.session['carrito'] = carrito
        messages.success(request, f"Menú del día agregado. Ahorras ${descuento_menu:,.0f}")
    else:
        messages.error(request, "El menú del día no tiene descuento disponible")
    
    return redirect('carrito')


@login_required
def crear_pedido(request):
    """Crea un nuevo pedido"""
    if request.method == 'POST':
        # Obtener datos del formulario
        tipo_pedido = request.POST.get('tipo_pedido', 'S')
        metodo_pago = request.POST.get('metodo_pago', 'EF')
        direccion_entrega = request.POST.get('direccion_entrega', '')
        telefono_contacto = request.POST.get('telefono_contacto', '')
        notas_entrega = request.POST.get('notas_entrega', '')
        
        # Obtener items del carrito
        carrito = request.session.get('carrito', [])
        
        if not carrito:
            messages.error(request, "Tu carrito está vacío")
            return redirect('carrito')
        
        # Calcular subtotal
        subtotal = Decimal('0')
        items_pedido = []
        
        for item in carrito:
            producto = Producto.objects.get(id=item['producto_id'])
            cantidad = int(item['cantidad'])
            precio = producto.get_precio_con_descuento()
            items_pedido.append({
                'producto': producto,
                'cantidad': cantidad,
                'precio': precio,
                'subtotal': precio * cantidad
            })
            subtotal += precio * cantidad
        
        # Calcular descuentos
        descuento = 0
        descuento_puntos = 0
        descuento_cupon = 0
        descuento_beneficios = 0
        
        # Aplicar cupón si hay
        cupon_data = request.session.get('cupon_aplicado')
        if cupon_data:
            try:
                cupon = Cupon.objects.get(codigo__iexact=cupon_data['codigo'])
                if cupon.valor_minimo is None or subtotal >= cupon.valor_minimo:
                    descuento_cupon = cupon.aplicar_descuento(subtotal)
                    # Marcar cupón como usado
                    cupon.usos_actuales += 1
                    cupon.save()
            except Cupon.DoesNotExist:
                pass
        
        # Aplicar puntos si hay
        puntos_data = request.session.get('puntos_aplicados')
        if puntos_data:
            descuento_puntos = puntos_data['descuento']
            # Restar puntos del usuario
            try:
                perfil = request.user.perfil
                perfil.puntos_fidelidad -= puntos_data['puntos']
                perfil.save()
            except Perfil.DoesNotExist:
                pass
        
        # Aplicar descuento del menu del dia
        descuento_menu_dia = Decimal(str(request.session.get('descuento_menu_dia', 0)))
        
        # Procesar beneficios canjeados - solo descuento
        beneficios_session = request.session.get('beneficios_canjeados', [])
        if beneficios_session:
            # Si es un descuento (tipo D) o tiene porcentaje mayor a 0, aplicarlo
            for benef in beneficios_session:
                if benef['tipo'] == 'D' or (benef['tipo'] == 'P' and benef['porcentaje'] > 0):
                    descuento_benef = subtotal * (Decimal(str(benef['porcentaje'])) / 100)
                    descuento_beneficios += descuento_benef
        
        # Calcular descuento total
        descuento_total = descuento + descuento_cupon + Decimal(str(descuento_puntos)) + descuento_beneficios + descuento_menu_dia
        
        # Calcular costo de domicilio si aplica
        costo_domicilio = Decimal('0')
        if tipo_pedido == 'D':
            costo_domicilio = Decimal('5000')
        
        # Calcular total
        total = subtotal - descuento_total + costo_domicilio
        
        # Obtener latitud y longitud
        latitud = request.POST.get('latitud')
        longitud = request.POST.get('longitud')
        
        # Crear el pedido
        pedido = Pedido.objects.create(
            cliente=request.user,
            tipo_pedido=tipo_pedido,
            metodo_pago=metodo_pago,
            direccion_entrega=direccion_entrega,
            telefono_contacto=telefono_contacto,
            notas_entrega=notas_entrega,
            subtotal=subtotal,
            descuento=descuento_total,
            descuento_puntos=descuento_puntos,
            costo_domicilio=costo_domicilio,
            total=total,
            latitud=latitud if latitud else None,
            longitud=longitud if longitud else None
        )
        
        # Crear los items del pedido
        for item in items_pedido:
            ItemPedido.objects.create(
                pedido=pedido,
                producto=item['producto'],
                cantidad=item['cantidad'],
                precio_unitario=item['precio'],
                subtotal=item['subtotal']
            )
        
        # Agregar notas sobre el menú del día si aplica
        if descuento_menu_dia > 0:
            if pedido.notas:
                pedido.notas = pedido.notas + ' | Menu del dia'
            else:
                pedido.notas = 'Menu del dia'
            pedido.save()
        
        # Limpiar el carrito y la sesión
        request.session['carrito'] = []
        request.session.pop('cupon_aplicado', None)
        request.session.pop('puntos_aplicados', None)
        request.session.pop('descuento_menu_dia', None)
        request.session.pop('beneficios_canjeados', None)
        
        # Registrar el cupón usado por el usuario
        if cupon_data:
            try:
                perfil = request.user.perfil
                cupones_usados = perfil.cupones_usados or []
                # Normalizar a mayúsculas para mantener consistencia
                codigo_upper = cupon_data['codigo'].upper()
                # Verificar si ya está en la lista (evitar duplicados)
                if codigo_upper.upper() not in [c.upper() for c in cupones_usados]:
                    cupones_usados.append(codigo_upper)
                    perfil.cupones_usados = cupones_usados
                    perfil.save(update_fields=['cupones_usados'])
            except Perfil.DoesNotExist:
                pass
        
        # Calcular puntos de fidelidad (1.25% del total - reducido a la mitad)
        puntos_ganados = int(total * Decimal('0.0125'))
        pedido.puntos_ganados = puntos_ganados
        
        # Agregar puntos al cliente y recalcular nivel
        try:
            perfil = request.user.perfil
            perfil.puntos_fidelidad += puntos_ganados
            perfil.total_pedidos += 1
            perfil.ultimo_pedido = timezone.now()
            perfil.gasto_total += total
            # Llamar al método para recalcular el nivel
            perfil.calcular_nivel()
        except Perfil.DoesNotExist:
            pass
        
        pedido.save()
        
        messages.success(request, f"Pedido #{pedido.numero_pedido} creado exitosamente. Has ganado {puntos_ganados} puntos!")
        return redirect('detalle_pedido', pedido_id=pedido.id)
    
    return redirect('carrito')


def detalle_pedido(request, pedido_id):
    """Muestra el detalle de un pedido"""
    pedido = get_object_or_404(Pedido, id=pedido_id)
    
    # Verificar que el usuario sea el propietario o un admin
    if pedido.cliente != request.user and not request.user.is_staff:
        messages.error(request, "No tienes permiso para ver este pedido")
        return redirect('inicio')
    
    return render(request, 'pedidos/detalle_pedido.html', {'pedido': pedido})


def generar_factura_pdf(request, pedido_id):
    """Genera una factura en PDF para un pedido"""
    pedido = get_object_or_404(Pedido, id=pedido_id)
    
    # Verificar permisos
    if pedido.cliente != request.user and not request.user.is_staff:
        messages.error(request, "No tienes permiso para ver esta factura")
        return redirect('inicio')
    
    # Crear el PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="factura_{pedido.numero_pedido}.pdf"'
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
    
    # Estilos
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#d35400'),
        spaceAfter=30,
        alignment=1
    )
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#2c3e50'),
        spaceBefore=20,
        spaceAfter=10
    )
    normal_style = styles['Normal']
    
    # Contenido
    story = []
    
    # Título
    story.append(Paragraph("Restaurante Sabor Colombiano", title_style))
    story.append(Paragraph(f"Factura #{pedido.numero_pedido}", subtitle_style))
    story.append(Spacer(1, 20))
    
    # Información del cliente
    story.append(Paragraph(f"<b>Cliente:</b> {pedido.cliente.get_full_name() or pedido.cliente.username}", normal_style))
    story.append(Paragraph(f"<b>Fecha:</b> {pedido.fecha_pedido.strftime('%d/%m/%Y %H:%M')}", normal_style))
    story.append(Paragraph(f"<b>Tipo:</b> {'Domicilio' if pedido.tipo_pedido == 'D' else 'En el restaurante'}", normal_style))
    story.append(Paragraph(f"<b>Método de pago:</b> {pedido.get_metodo_pago_display()}", normal_style))
    
    if pedido.direccion_entrega:
        story.append(Paragraph(f"<b>Dirección de entrega:</b> {pedido.direccion_entrega}", normal_style))
    
    story.append(Spacer(1, 20))
    
    # Tabla de items
    data = [['Producto', 'Cantidad', 'Precio', 'Subtotal']]
    for item in pedido.items.all():
        data.append([
            item.producto.nombre,
            str(item.cantidad),
            f"${item.precio_unitario:,.0f}",
            f"${item.subtotal:,.0f}"
        ])
    
    table = Table(data, colWidths=[3*inch, 1*inch, 1.5*inch, 1.5*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#d35400')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(table)
    story.append(Spacer(1, 20))
    
    # Totales
    story.append(Paragraph(f"<b>Subtotal:</b> ${pedido.subtotal:,.0f}", normal_style))
    
    if pedido.descuento > 0:
        story.append(Paragraph(f"<b>Descuento:</b> -${pedido.descuento:,.0f}", normal_style))
    if pedido.descuento_puntos > 0:
        story.append(Paragraph(f"<b>Descuento Puntos ({pedido.puntos_canjeados}):</b> -${pedido.descuento_puntos:,.0f}", normal_style))
    if pedido.costo_domicilio > 0:
        story.append(Paragraph(f"<b>Costo de domicilio:</b> ${pedido.costo_domicilio:,.0f}", normal_style))
    
    story.append(Paragraph(f"<b>TOTAL:</b> ${pedido.total:,.0f}", subtitle_style))
    
    # Puntos ganados
    if pedido.puntos_ganados > 0:
        story.append(Spacer(1, 20))
        story.append(Paragraph(f"<b>Puntos ganados:</b> {pedido.puntos_ganados}", normal_style))
    
    # Pie de página
    story.append(Spacer(1, 30))
    story.append(Paragraph("=" * 50, normal_style))
    story.append(Paragraph("Gracias por preferirnos!", normal_style))
    story.append(Paragraph(f"Documento generado el {datetime.now().strftime('%d/%m/%Y %H:%M')}", normal_style))
    
    # Construir PDF
    doc.build(story)
    pdf = buffer.getvalue()
    buffer.close()
    
    response.write(pdf)
    return response


@login_required
def historial_pedidos(request):
    """Muestra el historial de pedidos del usuario"""
    pedidos = Pedido.objects.filter(cliente=request.user).order_by('-fecha_pedido')
    return render(request, 'usuarios/mis_pedidos.html', {'pedidos': pedidos})


@login_required
def dashboard_pedidos(request):
    """Dashboard de pedidos para administración"""
    if not request.user.is_staff:
        messages.error(request, "No tienes permiso para acceder a esta página")
        return redirect('inicio')
    
    # Estadísticas generales
    total_pedidos = Pedido.objects.count()
    pedidos_hoy = Pedido.objects.filter(fecha_pedido__date=date.today()).count()
    ingresos_hoy = Pedido.objects.filter(
        fecha_pedido__date=date.today(),
        estado__in=['C', 'E', 'R', 'F']
    ).aggregate(Sum('total'))['total__sum'] or 0
    
    # Pedidos por estado
    pedidos_pendientes = Pedido.objects.filter(estado='P').count()
    pedidos_confirmados = Pedido.objects.filter(estado='C').count()
    pedidos_preparacion = Pedido.objects.filter(estado='E').count()
    pedidos_listos = Pedido.objects.filter(estado='R').count()
    pedidos_entregados = Pedido.objects.filter(estado='F').count()
    
    # Productos más vendidos
    productos_mas_vendidos = ItemPedido.objects.values(
        'producto__nombre'
    ).annotate(
        total_vendido=Sum('cantidad')
    ).order_by('-total_vendido')[:10]
    
    # Clientes más frecuentes
    clientes_frecuentes = Pedido.objects.values(
        'cliente__username',
        'cliente__first_name',
        'cliente__last_name'
    ).annotate(
        total_pedidos=Count('id')
    ).order_by('-total_pedidos')[:10]
    
    context = {
        'total_pedidos': total_pedidos,
        'pedidos_hoy': pedidos_hoy,
        'ingresos_hoy': ingresos_hoy,
        'pedidos_pendientes': pedidos_pendientes,
        'pedidos_confirmados': pedidos_confirmados,
        'pedidos_preparacion': pedidos_preparacion,
        'pedidos_listos': pedidos_listos,
        'pedidos_entregados': pedidos_entregados,
        'productos_mas_vendidos': productos_mas_vendidos,
        'clientes_frecuentes': clientes_frecuentes,
    }
    
    return render(request, 'pedidos/dashboard.html', context)

