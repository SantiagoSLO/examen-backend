from django.urls import path
from . import views
from .api import CategoriaListCreateView, CategoriaDetailView, ProductoListCreateView, ProductoDetailView

urlpatterns = [
    # Carta del restaurante
    path('carta/', views.CartaView.as_view(), name='carta'),
    path('carta/descargar/', views.generar_pdf_carta, name='descargar_carta_pdf'),
    
    # Categorías
    path('categoria/<int:pk>/', views.CategoriaDetailView.as_view(), name='categoria_detail'),
    
    # Productos
    path('producto/<int:pk>/', views.ProductoDetailView.as_view(), name='producto_detail'),
    
    # Búsqueda
    path('buscar/', views.buscar_productos, name='buscar'),
    
    # Menú del día
    path('menu-del-dia/', views.menu_del_dia_view, name='menu_del_dia'),
    
    # Promociones
    path('promociones/', views.promociones_view, name='promociones'),
    
    # API
    path('api/categorias/', CategoriaListCreateView.as_view(), name='categoria-list'),
    path('api/categorias/<int:pk>/', CategoriaDetailView.as_view(), name='categoria-detail'),
    path('api/productos/', ProductoListCreateView.as_view(), name='producto-list'),
    path('api/productos/<int:pk>/', ProductoDetailView.as_view(), name='producto-detail'),
]
