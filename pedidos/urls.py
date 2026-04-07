from django.urls import path
from . import views

urlpatterns = [
    # Carrito
    path('carrito/', views.ver_carrito, name='carrito'),
    path('carrito/agregar/<int:producto_id>/', views.agregar_al_carrito, name='agregar_carrito'),
    path('carrito/actualizar/<str:item_id>/', views.actualizar_carrito, name='actualizar_carrito'),
    path('carrito/eliminar/<str:item_id>/', views.eliminar_del_carrito, name='eliminar_carrito'),
    path('carrito/aplicar-puntos/', views.aplicar_puntos, name='aplicar_puntos'),
    path('carrito/agregar-menu-dia/', views.agregar_menu_dia, name='agregar_menu_dia'),
    
    # Pedidos
    path('pedido/crear/', views.crear_pedido, name='crear_pedido'),
    path('pedido/<int:pedido_id>/', views.detalle_pedido, name='detalle_pedido'),
    path('pedido/<int:pedido_id>/factura/', views.generar_factura_pdf, name='factura_pdf'),
    path('pedidos/historial/', views.historial_pedidos, name='historial_pedidos'),
    
    # Dashboard
    path('dashboard/pedidos/', views.dashboard_pedidos, name='dashboard_pedidos'),
]
