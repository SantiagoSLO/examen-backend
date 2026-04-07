from django.core.management.base import BaseCommand
from menu.models import Categoria, Producto, Promocion
from django.utils import timezone
from datetime import datetime, timedelta


class Command(BaseCommand):
    help = 'Carga los platos típicos de Colombia en la base de datos'

    def handle(self, *args, **options):
        self.stdout.write('Cargando platos típicos de Colombia...')
        
        # Crear categorías
        categorias_data = [
            {
                'nombre': 'Platos Principales',
                'descripcion': 'Los platos típicos más representativos de Colombia',
                'orden': 1
            },
            {
                'nombre': 'Bebidas',
                'descripcion': 'Refrescantes bebidas tradicionales colombianas',
                'orden': 2
            },
            {
                'nombre': 'Postres',
                'descripcion': 'Deliciosos postres típicos colombianos',
                'orden': 3
            },
            {
                'nombre': 'Acompañamientos',
                'descripcion': 'Acompañamientos perfectos para tus platos',
                'orden': 4
            },
            {
                'nombre': 'Entradas',
                'descripcion': 'Deliciosas entradas para comenzar tu comida',
                'orden': 5
            }
        ]
        
        # Crear o obtener categorías
        categorias = {}
        for cat_data in categorias_data:
            cat, created = Categoria.objects.get_or_create(
                nombre=cat_data['nombre'],
                defaults={
                    'descripcion': cat_data['descripcion'],
                    'orden': cat_data['orden'],
                    'activa': True
                }
            )
            categorias[cat_data['nombre']] = cat
            if created:
                self.stdout.write(f'  - Categoría "{cat.nombre}" creada')
        
        # Obtener categorías
        principales = categorias['Platos Principales']
        bebidas = categorias['Bebidas']
        postres = categorias['Postres']
        acompanamientos = categorias['Acompañamientos']
        entradas = categorias['Entradas']
        
        # Platos principales
        platos_principales = [
            {
                'nombre': 'Bandeja Paisa',
                'descripcion': 'El plato más representativo de Colombia. Incluye frijoles, arroz, carne molida, chicharrón, huevo frito, arepa, plátano y aguacate.',
                'precio': 28000,
                'tiempo_preparacion': 25,
                'orden': 1
            },
            {
                'nombre': 'Ajiaco Santandereano',
                'descripcion': 'Sopa tradicional de papa con espinazo de cerdo, mazorca, guacamole y arroz.',
                'precio': 18000,
                'tiempo_preparacion': 20,
                'orden': 2
            },
            {
                'nombre': 'Sancocho de Gallina',
                'descripcion': 'Sopa tradicional con gallina, plátano, yuca, papa y cilantro. Perfecto para compartir.',
                'precio': 22000,
                'tiempo_preparacion': 30,
                'orden': 3
            },
            {
                'nombre': 'Changua',
                'descripcion': 'Sopa de leche con huevo, cebolla, cilantro y arepa. Desayuno típico boyacense.',
                'precio': 12000,
                'tiempo_preparacion': 15,
                'orden': 4
            },
            {
                'nombre': 'Mute Samario',
                'descripcion': 'Sopa de carne de res con garbanzos, papa, mazorca yucas. De la costa caribe.',
                'precio': 20000,
                'tiempo_preparacion': 25,
                'orden': 5
            },
            {
                'nombre': 'Olla a la Criolla',
                'descripcion': 'Sopa espesa con carne de res, pollo, chorizo, tocino, zanahoria, papa y plátano.',
                'precio': 23000,
                'tiempo_preparacion': 30,
                'orden': 6
            },
            {
                'nombre': 'Pescado Frito',
                'descripcion': 'Pescado fresco frito acompañado de arroz, patacones y salsa de ají.',
                'precio': 32000,
                'tiempo_preparacion': 20,
                'orden': 7
            },
            {
                'nombre': 'Mujerre',
                'descripcion': 'Planco de mujer soltera acompañado de arroz, frijoles, arepa y chutney.',
                'precio': 25000,
                'tiempo_preparacion': 25,
                'orden': 8
            },
            {
                'nombre': 'Cuy Asado',
                'descripcion': 'Cuy frito típico de Nariño, acompañado de papas y ají.',
                'precio': 35000,
                'tiempo_preparacion': 35,
                'orden': 9
            },
            {
                'nombre': 'Tamales Tolimenses',
                'descripcion': 'Masa de maíz rellena de carne, pollo, huevo, zanahoria, garbanzos, envuelto en hoja de plátano.',
                'precio': 15000,
                'tiempo_preparacion': 15,
                'orden': 10
            },
        ]
        
        # Bebidas
        bebidas_data = [
            {
                'nombre': 'Agua de Panela con Queso',
                'descripcion': 'Bebida caliente de panela con queso fresco.',
                'precio': 5000,
                'tiempo_preparacion': 5,
                'orden': 1
            },
            {
                'nombre': 'Champús',
                'descripcion': 'Bebida fría de maíz, naranja, lulo y panela. Refrescante y tradicional.',
                'precio': 6000,
                'tiempo_preparacion': 5,
                'orden': 2
            },
            {
                'nombre': 'Avena Cold',
                'descripcion': 'Bebida fría de avena con vainilla y canela.',
                'precio': 5500,
                'tiempo_preparacion': 5,
                'orden': 3
            },
            {
                'nombre': 'Lulada',
                'descripcion': 'Bebida refrescante de lulo con hielo y azúcar.',
                'precio': 5500,
                'tiempo_preparacion': 3,
                'orden': 4
            },
            {
                'nombre': 'Jugo de Gulupa',
                'descripcion': 'Jugo natural de gulupa (maracuyá morado).',
                'precio': 5000,
                'tiempo_preparacion': 3,
                'orden': 5
            },
            {
                'nombre': 'Café Colombiano',
                'descripcion': 'Café aromático colombiano preparado al estilo tradicional.',
                'precio': 4000,
                'tiempo_preparacion': 5,
                'orden': 6
            },
            {
                'nombre': 'Chocolate con Panela',
                'descripcion': 'Chocolate caliente de cacao con panela y queso.',
                'precio': 6000,
                'tiempo_preparacion': 8,
                'orden': 7
            },
            {
                'nombre': 'Masato de Arracacha',
                'descripcion': 'Bebida fermentada de arracacha, tradicional del Valle.',
                'precio': 5500,
                'tiempo_preparacion': 5,
                'orden': 8
            },
        ]
        
        # Postres
        postres_data = [
            {
                'nombre': 'Postre de Natillas',
                'descripcion': 'Natillas con bocadillo y crema de leche.',
                'precio': 6000,
                'tiempo_preparacion': 5,
                'orden': 1
            },
            {
                'nombre': 'Arequipe',
                'descripcion': 'Dulce de leche caramelizado típico colombiano.',
                'precio': 5000,
                'tiempo_preparacion': 3,
                'orden': 2
            },
            {
                'nombre': 'Tortica de Promesa',
                'descripcion': 'Bizcocho de Fécula de maíz con relleno de arequipe.',
                'precio': 7000,
                'tiempo_preparacion': 5,
                'orden': 3
            },
            {
                'nombre': 'Obleas con Arequipe',
                'descripcion': 'Obleas de vainilla rellenas de arequipe y queso.',
                'precio': 5500,
                'tiempo_preparacion': 3,
                'orden': 4
            },
            {
                'nombre': 'Dulce de Membrillo',
                'descripcion': 'Dulce tradicional de membrillo.',
                'precio': 4500,
                'tiempo_preparacion': 3,
                'orden': 5
            },
            {
                'nombre': 'Truffles de Chocolate',
                'descripcion': 'Trufas de chocolate con cacao en polvo.',
                'precio': 6500,
                'tiempo_preparacion': 5,
                'orden': 6
            },
        ]
        
        # Acompañamientos
        acompanamientos_data = [
            {
                'nombre': 'Patacones',
                'descripcion': 'Plátanos verdes fritos, ideales para acompañar.',
                'precio': 6000,
                'tiempo_preparacion': 10,
                'orden': 1
            },
            {
                'nombre': 'Yuca Frita',
                'descripcion': 'Yuca crocante frita con sal.',
                'precio': 5000,
                'tiempo_preparacion': 10,
                'orden': 2
            },
            {
                'nombre': 'Papas Criollas',
                'descripcion': 'Papas pequeñas fritas doradas.',
                'precio': 5000,
                'tiempo_preparacion': 10,
                'orden': 3
            },
            {
                'nombre': 'Arroz con Coco',
                'descripcion': 'Arroz preparado con leche de coco.',
                'precio': 5500,
                'tiempo_preparacion': 15,
                'orden': 4
            },
            {
                'nombre': 'Frijoles Negros',
                'descripcion': 'Frijoles negros cocidos al estilo colombiano.',
                'precio': 5000,
                'tiempo_preparacion': 10,
                'orden': 5
            },
            {
                'nombre': 'Ensalada de Aguacate',
                'descripcion': 'Aguacate fresco con tomate y cebolla.',
                'precio': 6000,
                'tiempo_preparacion': 5,
                'orden': 6
            },
        ]
        
        # Entradas
        entradas_data = [
            {
                'nombre': 'Empanadas',
                'descripcion': 'Empanadas de carne molida fritas, acompañada de salsa de ají.',
                'precio': 8000,
                'tiempo_preparacion': 10,
                'orden': 1
            },
            {
                'nombre': 'Arepas de Queso',
                'descripcion': 'Arepas de maíz rellenas de queso.',
                'precio': 6000,
                'tiempo_preparacion': 8,
                'orden': 2
            },
            {
                'nombre': 'Buñuelos',
                'descripcion': 'Buñuelos de queso fritos, crujientes por fuera y suaves por dentro.',
                'precio': 7000,
                'tiempo_preparacion': 10,
                'orden': 3
            },
            {
                'nombre': 'Arepa de Choclo',
                'descripcion': 'Arepa dulce de maíz tierno.',
                'precio': 5000,
                'tiempo_preparacion': 8,
                'orden': 4
            },
            {
                'nombre': 'Sopa de Caracol',
                'descripcion': 'Sopa ligera de caracol terrestre.',
                'precio': 12000,
                'tiempo_preparacion': 15,
                'orden': 5
            },
            {
                'nombre': 'Cazuela de Fríjoles',
                'descripcion': 'Cazuela tradicional de frijoles.',
                'precio': 10000,
                'tiempo_preparacion': 12,
                'orden': 6
            },
        ]
        
        # Crear productos
        productos_creados = 0
        
        for plato in platos_principales:
            Producto.objects.get_or_create(
                nombre=plato['nombre'],
                defaults={
                    'descripcion': plato['descripcion'],
                    'precio': plato['precio'],
                    'categoria': principales,
                    'tipo_producto': 'P',
                    'disponible': True,
                    'tiempo_preparacion': plato['tiempo_preparacion'],
                    'orden': plato['orden']
                }
            )
            productos_creados += 1
        
        for plato in bebidas_data:
            Producto.objects.get_or_create(
                nombre=plato['nombre'],
                defaults={
                    'descripcion': plato['descripcion'],
                    'precio': plato['precio'],
                    'categoria': bebidas,
                    'tipo_producto': 'B',
                    'disponible': True,
                    'tiempo_preparacion': plato['tiempo_preparacion'],
                    'orden': plato['orden']
                }
            )
            productos_creados += 1
        
        for plato in postres_data:
            Producto.objects.get_or_create(
                nombre=plato['nombre'],
                defaults={
                    'descripcion': plato['descripcion'],
                    'precio': plato['precio'],
                    'categoria': postres,
                    'tipo_producto': 'D',
                    'disponible': True,
                    'tiempo_preparacion': plato['tiempo_preparacion'],
                    'orden': plato['orden']
                }
            )
            productos_creados += 1
        
        for plato in acompanamientos_data:
            Producto.objects.get_or_create(
                nombre=plato['nombre'],
                defaults={
                    'descripcion': plato['descripcion'],
                    'precio': plato['precio'],
                    'categoria': acompanamientos,
                    'tipo_producto': 'A',
                    'disponible': True,
                    'tiempo_preparacion': plato['tiempo_preparacion'],
                    'orden': plato['orden']
                }
            )
            productos_creados += 1
        
        for plato in entradas_data:
            Producto.objects.get_or_create(
                nombre=plato['nombre'],
                defaults={
                    'descripcion': plato['descripcion'],
                    'precio': plato['precio'],
                    'categoria': entradas,
                    'tipo_producto': 'O',
                    'disponible': True,
                    'tiempo_preparacion': plato['tiempo_preparacion'],
                    'orden': plato['orden']
                }
            )
            productos_creados += 1
        
        # Crear una promoción de ejemplo
        Promo, created = Promocion.objects.get_or_create(
            codigo='BIENVENIDO20',
            defaults={
                'titulo': '20% de Descuento en Platos Principales',
                'descripcion': 'Aprovecha nuestro descuento especial en todos los platos principales. Ideal para compartir en familia.',
                'porcentaje': 20,
                'fecha_inicio': timezone.now(),
                'fecha_fin': timezone.now() + timedelta(days=30),
                'activa': True,
            }
        )
        
        # Agregar productos a la promoción
        if created:
            for producto in Producto.objects.filter(categoria=principales)[:5]:
                Promo.productos.add(producto)
        
        self.stdout.write(f'OK Se crearon {productos_creados} productos y categorias')
        if created:
            self.stdout.write(f'OK Se creo la promocion "Bienvenido"')
        else:
            self.stdout.write(f'La promocion ya existia')
        self.stdout.write('La carta de comida tipica colombiana esta lista!')
