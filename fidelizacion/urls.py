from django.urls import path
from . import views

urlpatterns = [
    path('programa/', views.programa_fidelidad, name='programa_fidelidad'),
    path('canjear/<int:beneficio_id>/', views.canjear_beneficio, name='canjear_beneficio'),
    path('aplicar-cupon/', views.aplicar_cupon, name='aplicar_cupon'),
    path('estadisticas/', views.estadisticas_fidelizacion, name='estadisticas_fidelizacion'),
]
