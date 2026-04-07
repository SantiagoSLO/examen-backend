"""
URL configuration for restaurante project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Panel de Administración
    path('admin/', admin.site.urls),
    
    # URLs de las aplicaciones
    path('', include('usuarios.urls')),
    path('menu/', include('menu.urls')),
    path('pedidos/', include('pedidos.urls')),
    path('fidelizacion/', include('fidelizacion.urls')),
]

# Servir archivos estáticos y media en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
