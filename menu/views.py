from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.views.generic import ListView, DetailView
from django.db.models import Q, Prefetch
from django.db import models
from .models import Categoria, Producto, Promocion, MenuDelDia
from fidelizacion.models import Cupon
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from io import BytesIO
from django.utils import timezone
from datetime import datetime, date
from decimal import Decimal
import random


class CartaView(ListView):
    """Vista pública de la carta del restaurante"""
    model = Categoria
    template_name = 'menu/carta.html'
    context_object_name = 'categorias'
    
    def get_queryset(self):
        return Categoria.objects.filter(activa=True).prefetch_related(
            Prefetch(
                'productos',
                queryset=Producto.objects.filter(disponible=True).order_by('orden', 'nombre')
            )
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['promociones'] = Promocion.objects.filter(
            activa=True,
            fecha_inicio__lte=timezone.now(),
            fecha_fin__gte=timezone.now()
        )
        return context


class CategoriaDetailView(DetailView):
    """Vista de detalle de una categoría"""
    model = Categoria
    template_name = 'menu/categoria.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['productos'] = self.object.productos.filter(disponible=True).order_by('orden', 'nombre')
        return context


class ProductoDetailView(DetailView):
    """Vista de detalle de un producto"""
    model = Producto
    template_name = 'menu/producto.html'
    context_object_name = 'producto'


def buscar_productos(request):
    """Búsqueda de productos"""
    query = request.GET.get('q', '')
    categoria = request.GET.get('categoria', '')
    
    productos = Producto.objects.filter(disponible=True)
    
    if query:
        productos = productos.filter(
            Q(nombre__icontains=query) | 
            Q(descripcion__icontains=query)
        )
    
    if categoria:
        productos = productos.filter(categoria_id=categoria)
    
    categorias = Categoria.objects.filter(activa=True)
    
    return render(request, 'menu/buscar.html', {
        'productos': productos,
        'categorias': categorias,
        'query': query,
        'categoria_seleccionada': categoria
    })


def menu_del_dia_view(request):
    """Vista del menu del dia"""
    hoy = date.today()
    menu = MenuDelDia.objects.filter(fecha=hoy, disponible=True).first()
    
    # Si no hay menu para hoy, generar uno automaticamente
    if not menu:
        # Obtener productos disponibles
        entradas = list(Producto.objects.filter(
            disponible=True,
            tipo_producto__in=['A', 'O']
        ))
        principales = list(Producto.objects.filter(
            disponible=True,
            tipo_producto='P'
        ))
        bebidas = list(Producto.objects.filter(
            disponible=True,
            tipo_producto='B'
        ))
        postres = list(Producto.objects.filter(
            disponible=True,
            tipo_producto='D'
        ))
        
        if entradas and principales and bebidas and postres:
            # Seleccionar productos aleatorios basados en el dia
            random.seed(hoy.toordinal())
            
            menu = MenuDelDia.objects.create(
                fecha=hoy,
                entrada=random.choice(entradas),
                plato_principal=random.choice(principales),
                bebida=random.choice(bebidas),
                postre=random.choice(postres),
                precio_especial=0,
                disponible=True,
                notas="Menu del dia generado automaticamente"
            )
            
            # Calcular precio especial (80% del precio individual)
            precio_total = (
                menu.entrada.precio + 
                menu.plato_principal.precio + 
                menu.bebida.precio + 
                menu.postre.precio
            )
            menu.precio_especial = precio_total * Decimal('0.80')
            menu.save()
    
    return render(request, 'menu/menu_del_dia.html', {'menu': menu, 'fecha': hoy})


def generar_pdf_carta(request):
    """Genera un PDF con la carta del restaurante"""
    from django.db import models
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="carta_restaurante.pdf"'
    
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
    
    # Titulo
    story.append(Paragraph("Restaurante Sabor Colombiano", title_style))
    story.append(Paragraph("Carta de Productos", subtitle_style))
    story.append(Spacer(1, 20))
    
    # Informacion de contacto
    story.append(Paragraph("Direccion: Calle Principal #123, Ciudad", normal_style))
    story.append(Paragraph("Telefono: (123) 456-7890", normal_style))
    story.append(Paragraph("Horario: Lun-Dom 11:00 AM - 10:00 PM", normal_style))
    story.append(Spacer(1, 30))
    
    # Categorias y productos
    categorias = Categoria.objects.filter(activa=True).prefetch_related('productos')
    
    for categoria in categorias:
        productos = categoria.productos.filter(disponible=True).order_by('orden', 'nombre')
        if productos:
            story.append(Paragraph(f"{categoria.nombre}", subtitle_style))
            
            if categoria.descripcion:
                story.append(Paragraph(categoria.descripcion, normal_style))
            
            # Tabla de productos
            data = [['Producto', 'Descripcion', 'Precio']]
            for producto in productos:
                precio = f"${producto.precio:,.0f}"
                desc = producto.descripcion[:50] + "..." if len(producto.descripcion) > 50 else producto.descripcion
                data.append([producto.nombre, desc, precio])
            
            table = Table(data, colWidths=[1.5*inch, 3*inch, 1*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#d35400')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (-1, 0), (-1, -1), 'RIGHT'),
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
    
    # Pie de pagina
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


def promociones_view(request):
    """Vista de promociones"""
    from django.utils import timezone
    
    promociones = Promocion.objects.filter(
        activa=True,
        fecha_inicio__lte=timezone.now(),
        fecha_fin__gte=timezone.now()
    )
    
    # Obtener cupones activos
    hoy = timezone.now().date()
    cupones = Cupon.objects.filter(activo=True).filter(
        models.Q(fecha_inicio__isnull=True) | models.Q(fecha_inicio__lte=hoy)
    ).filter(
        models.Q(fecha_fin__isnull=True) | models.Q(fecha_fin__gte=hoy)
    ).filter(
        models.Q(usos_maximos__isnull=True) | models.Q(usos_actuales__lt=models.F('usos_maximos'))
    )
    
    # Si el usuario está autenticado, filtrar los cupones que ya ha usado
    cupones_usuario = []
    if request.user.is_authenticated:
        try:
            perfil = request.user.perfil
            cupones_usuario = perfil.cupones_usados or []
            # Excluir los cupones que el usuario ya ha usado
            cupones = cupones.exclude(codigo__in=cupones_usuario)
        except:
            pass
    
    return render(request, 'menu/promociones.html', {
        'promociones': promociones,
        'cupones': cupones
    })
