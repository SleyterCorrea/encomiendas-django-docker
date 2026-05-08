# Sistema de Gestión de Encomiendas

Proyecto académico desarrollado en Django con Docker. Cubre desde los modelos y vistas tradicionales hasta una API REST completa con autenticación JWT.

---

## ¿Qué hace este sistema?

Es una aplicación web para gestionar el ciclo de vida de encomiendas: registro, seguimiento de estados (pendiente → en tránsito → entregado), historial de cambios y reportes. Tiene panel web con login de empleados y una API REST para integraciones externas.

---

## Stack

- **Python 3.11 / Django 5.2**
- **PostgreSQL 15** — base de datos principal
- **Redis 7** — caché para estadísticas
- **Docker + Docker Compose** — entorno de desarrollo reproducible
- **Django REST Framework** — API REST
- **SimpleJWT** — autenticación con tokens
- **drf-spectacular** — documentación OpenAPI / Swagger

---

## Levantar el proyecto

Requiere tener Docker instalado. Nada más.

```bash
git clone https://github.com/SleyterCorrea/encomiendas-django-docker.git
cd encomiendas-django-docker

# Copiar variables de entorno
cp .env.example .env

# Construir y levantar
docker compose build
docker compose up -d

# Migraciones y superusuario
docker compose exec web python manage.py migrate
docker compose exec web python manage.py createsuperuser
```

La app queda en `http://localhost:8001` y el admin en `http://localhost:8001/admin/`.

---

## Variables de entorno

El archivo `.env` necesita estas variables:

```
SECRET_KEY=cambia-esto-en-produccion
DEBUG=True
DB_NAME=encomiendas_db
DB_USER=encomiendas_user
DB_PASSWORD=encomiendas_pass
DB_HOST=db
DB_PORT=5432
REDIS_URL=redis://redis:6379/0
```

---

## API REST

La API vive en `/api/v1/`. Toda petición (excepto el login) requiere un token JWT en el header:

```
Authorization: Bearer <access_token>
```

### Obtener token

```bash
curl -X POST http://localhost:8001/api/v1/auth/token/ \
  -H 'Content-Type: application/json' \
  -d '{"username": "admin", "password": "tu_password"}'
```

La respuesta incluye `access` y `refresh`. El token de acceso dura 1 hora, el de refresco 7 días. El payload del JWT trae los datos del empleado directamente (código, cargo, nombre) para que el frontend no necesite hacer una petición extra.

### Documentación interactiva

- **Swagger UI**: `http://localhost:8001/api/docs/`
- **ReDoc**: `http://localhost:8001/api/redoc/`

### Endpoints principales

| Método | URL | Descripción |
|--------|-----|-------------|
| GET | `/api/v1/encomiendas/` | Lista paginada con filtros |
| POST | `/api/v1/encomiendas/` | Crear encomienda |
| GET | `/api/v1/encomiendas/{id}/` | Detalle con objetos anidados |
| PUT/PATCH | `/api/v1/encomiendas/{id}/` | Actualizar |
| DELETE | `/api/v1/encomiendas/{id}/` | Eliminar |
| POST | `/api/v1/encomiendas/{id}/cambiar_estado/` | Cambiar estado con historial |
| GET | `/api/v1/encomiendas/pendientes/` | Filtro rápido: solo pendientes |
| GET | `/api/v1/encomiendas/con_retraso/` | Encomiendas vencidas |
| GET | `/api/v1/encomiendas/estadisticas/` | Métricas generales (cacheado 15 min) |
| POST | `/api/v1/encomiendas/bulk_create/` | Crear múltiples de una vez |
| PATCH | `/api/v1/encomiendas/bulk_estado/` | Cambiar estado en lote |
| GET | `/api/v1/clientes/` | Clientes activos |
| GET | `/api/v1/rutas/` | Rutas disponibles |

### Filtros disponibles

```
/api/v1/encomiendas/?estado=PE
/api/v1/encomiendas/?search=Lima
/api/v1/encomiendas/?ordering=-fecha_registro
/api/v1/encomiendas/?desde=2026-01-01&hasta=2026-05-01
/api/v1/encomiendas/?con_retraso=true
/api/v1/encomiendas/?page=2&page_size=10
```

### API v2

Existe una versión simplificada en `/api/v2/encomiendas/` (solo lectura) que devuelve menos campos y agrega un campo `resumen` con el estado en texto legible.

---

## Permisos y seguridad

- Solo usuarios con un Empleado activo en la BD pueden usar la API (`EsEmpleadoActivo`)
- Los empleados regulares solo pueden modificar sus propias encomiendas (`EsPropietarioOAdmin`)
- Los usuarios staff/admin tienen acceso completo
- El campo `empleado_registro` y `observaciones` se ocultan para usuarios no-staff en la respuesta (`to_representation`)
- Throttling: 100 peticiones/hora para empleados, 5 intentos/minuto para login
- CORS habilitado para desarrollo

---

## Estructura del proyecto

```
├── config/          # Settings, URLs, choices globales
├── envios/          # App principal: modelos, vistas, serializers, viewsets, tests
├── clientes/        # App de clientes
├── rutas/           # App de rutas
├── api/             # Infraestructura de la API: filtros, paginación, permisos, throttles
│   └── v2/          # Versión 2 de la API
├── templates/       # Templates HTML del panel web
├── static/          # CSS, JS
└── docker-compose.yml
```

---

## Tests

```bash
docker compose exec web python manage.py test envios.tests.test_api --verbosity=2
```

16 tests que cubren: listado, creación, errores de validación (400), detalle anidado, cambio de estado, autenticación (401), filtros y estadísticas.

---

## Panel web

Además de la API, el proyecto tiene un panel web tradicional accesible en `/`:

- Login de empleados con sesión Django
- Dashboard con resumen de encomiendas
- CRUD de encomiendas con formularios
- Historial de cambios por encomienda
- Perfil del empleado

---

## Sesiones del proyecto

| Sesión | Tema |
|--------|------|
| 03 | Modelos Django ORM, QuerySets, validadores |
| 04 | Autenticación, sesiones, vistas protegidas |
| 05 | Django REST Framework — serializers, vistas genéricas, JWT |
| 06 | DRF avanzado — ViewSets, permisos, throttling, caché, tests |
