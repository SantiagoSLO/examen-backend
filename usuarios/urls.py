from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Autenticación
    path('login/', views.iniciar_sesion, name='login'),
    path('registro/', views.registro, name='registro'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    
    # Perfil de usuario
    path('perfil/', views.perfil_usuario, name='perfil'),
    path('mis-pedidos/', views.mis_pedidos, name='mis_pedidos'),
    path('mis-beneficios/', views.mis_beneficios, name='mis_beneficios'),
    
    # Inicio
    path('', views.InicioView.as_view(), name='inicio'),
]
