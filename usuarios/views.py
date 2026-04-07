from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.views.generic import TemplateView
from .models import Perfil


def registro(request):
    """Vista para el registro de nuevos usuarios"""
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            usuario = form.save()
            
            # Obtener o crear el perfil
            telefono = request.POST.get('telefono', '')
            try:
                perfil = usuario.perfil
                perfil.telefono = telefono
                perfil.save()
            except Perfil.DoesNotExist:
                # Crear nuevo perfil si no existe
                Perfil.objects.create(
                    usuario=usuario,
                    telefono=telefono
                )
            
            messages.success(request, '¡Registro exitoso! Bienvenido a Restaurante Sabor Colombiano. Ahora puedes hacer pedidos y ganar puntos de fidelidad.')
            login(request, usuario)
            return redirect('inicio')
        else:
            # Mostrar errores específicos del formulario
            for field in form:
                for error in field.errors:
                    messages.error(request, f"{error}")
            for error in form.non_field_errors():
                messages.error(request, f"{error}")
    else:
        form = UserCreationForm()
    return render(request, 'registration/registro.html', {'form': form})


def iniciar_sesion(request):
    """Vista para iniciar sesión"""
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            usuario = authenticate(username=username, password=password)
            if usuario is not None:
                login(request, usuario)
                messages.success(request, f'¡Bienvenido {username}!')
                return redirect('inicio')
            else:
                messages.error(request, 'Usuario o contraseña incorrectos.')
        else:
            messages.error(request, 'Usuario o contraseña incorrectos.')
    else:
        form = AuthenticationForm()
    return render(request, 'registration/login.html', {'form': form})


@login_required
def perfil_usuario(request):
    """Vista para ver y editar el perfil del usuario"""
    perfil = request.user.perfil
    
    if request.method == 'POST':
        # Actualizar datos del usuario
        request.user.first_name = request.POST.get('first_name', '')
        request.user.last_name = request.POST.get('last_name', '')
        request.user.email = request.POST.get('email', '')
        request.user.save()
        
        # Actualizar perfil
        perfil.telefono = request.POST.get('telefono', '')
        perfil.direccion = request.POST.get('direccion', '')
        perfil.numero_documento = request.POST.get('numero_documento', '')
        perfil.save()
        
        messages.success(request, 'Perfil actualizado correctamente.')
        return redirect('perfil')
    
    return render(request, 'usuarios/perfil.html', {'perfil': perfil})


@login_required
def mis_pedidos(request):
    """Vista para ver los pedidos del usuario"""
    from pedidos.models import Pedido
    pedidos = Pedido.objects.filter(cliente=request.user).order_by('-fecha_pedido')
    return render(request, 'usuarios/mis_pedidos.html', {'pedidos': pedidos})


@login_required
def mis_beneficios(request):
    """Vista para ver los beneficios del usuario"""
    perfil = request.user.perfil
    beneficios = perfil.get_beneficios_activos()
    return render(request, 'usuarios/mis_beneficios.html', {
        'beneficios': beneficios,
        'perfil': perfil
    })


class InicioView(TemplateView):
    """Vista de inicio del sitio público"""
    template_name = 'inicio.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from menu.models import Categoria, Producto, Promocion
        from fidelizacion.models import Beneficio
        
        context['categorias'] = Categoria.objects.filter(activa=True)
        context['promociones'] = Promocion.objects.filter(activa=True)
        context['beneficios'] = Beneficio.objects.filter(activo=True)[:5]
        
        # Si el usuario está autenticado, mostrar sus puntos
        if self.request.user.is_authenticated:
            context['perfil'] = self.request.user.perfil
            context['mis_beneficios'] = self.request.user.perfil.get_beneficios_activos()
        
        return context
