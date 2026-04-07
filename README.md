# Restaurante Backend

Backend API for the restaurant application built with Django and Django REST Framework.

## Features

- User management
- Menu management (categories, products)
- Order system
- Loyalty program
- API endpoints for frontend integration

## API Endpoints

- `/menu/api/categorias/` - List and create categories
- `/menu/api/productos/` - List and create products

## Deployment

Deployed on Render.

## Seed data on Render

If the backend starts with an empty database, use this command in Render:

```bash
python manage.py migrate && python manage.py cargar_carta && gunicorn restaurante.wsgi:application --bind 0.0.0.0:$PORT
```

This will create the restaurant menu data before the server starts.

## Setup

1. Clone the repo
2. Install dependencies: `pip install -r requirements.txt`
3. Run migrations: `python manage.py migrate`
4. Run server: `python manage.py runserver`

## CORS

Configured to allow requests from GitHub Pages.