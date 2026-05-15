# Sistema de Gestión de Encomiendas

Proyecto académico desarrollado en Django con Docker. Empezamos con modelos y vistas básicas, luego agregamos API REST con JWT, y en la sesión 7 integramos WebSockets para que el sistema sea reactivo en tiempo real.

---

## ¿Qué hace este sistema?

Aplicación web para gestionar encomiendas: registro, seguimiento de estados (pendiente → en tránsito → en destino → entregado), historial de cambios por empleado y estadísticas. Tiene panel web con login y una API REST completa. Desde la sesión 7, los cambios se propagan en tiempo real a todos los usuarios conectados sin recargar la página.

---

## Stack

- **Python 3.11 / Django 5.2**
- **PostgreSQL 15** — base de datos principal
- **Redis 7** — caché de estadísticas + Channel Layer para WebSockets
- **Docker + Docker Compose** — entorno reproducible
- **Django REST Framework** — API REST
- **SimpleJWT** — tokens de acceso y refresco
- **drf-spectacular** — documentación OpenAPI / Swagger
- **Django Channels + Daphne** — WebSockets y servidor ASGI
- **WhiteNoise** — archivos estáticos con servidor ASGI

---

## Levantar el proyecto

Solo necesitas Docker instalado.

```bash
git clone https://github.com/SleyterCorrea/encomiendas-django-docker.git
cd encomiendas-django-docker

cp .env.example .env

docker compose build
docker compose up -d

docker compose exec web python manage.py migrate
docker compose exec web python manage.py createsuperuser
```

La app queda en `http://localhost:8001` y el admin en `http://localhost:8001/admin/`.

## Cargar datos de prueba

```bash
docker compose exec web python manage.py seed_data
```

Crea 8 clientes, 8 rutas, 3 empleados y 8 encomiendas en distintos estados. Para limpiar todo y volver a cargar:

```bash
docker compose exec web python manage.py seed_data --clear
```

---

## Variables de entorno

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

## WebSockets — tiempo real (Sesión 07)

El sistema tiene tres canales WebSocket activos cuando entrás al dashboard:

| Endpoint WS | Descripción |
|-------------|-------------|
| `ws/dashboard/` | Actualiza los contadores (activas, en tránsito, retraso) automáticamente |
| `ws/encomienda/<pk>/` | Notifica cambios de estado en una encomienda específica |
| `ws/feed/` | Feed global — todos los empleados conectados ven cada cambio en vivo |

El badge "En vivo" en el dashboard indica que la conexión WebSocket está activa. Cuando cambiás el estado de una encomienda (desde el panel web o la API), el dashboard de cualquier otro usuario conectado se actualiza sin recargar.

El Channel Layer usa Redis en la base de datos 1 (`redis://redis:6379/1`) separada del caché (`redis://redis:6379/0`).

---

## API REST

Todos los endpoints (excepto login) requieren token JWT:

```
Authorization: Bearer <access_token>
```

### Obtener token

```bash
curl -X POST http://localhost:8001/api/v1/auth/token/ \
  -H 'Content-Type: application/json' \
  -d '{"username": "admin", "password": "tu_password"}'
```

El token dura 1 hora, el refresh 7 días.

### Documentación interactiva

- Swagger UI: `http://localhost:8001/api/docs/`
- ReDoc: `http://localhost:8001/api/redoc/`

### Endpoints principales

| Método | URL | Descripción |
|--------|-----|-------------|
| GET | `/api/v1/encomiendas/` | Lista paginada con filtros |
| POST | `/api/v1/encomiendas/` | Crear encomienda |
| GET | `/api/v1/encomiendas/{id}/` | Detalle con objetos anidados |
| PUT/PATCH | `/api/v1/encomiendas/{id}/` | Actualizar |
| DELETE | `/api/v1/encomiendas/{id}/` | Eliminar |
| POST | `/api/v1/encomiendas/{id}/cambiar_estado/` | Cambiar estado |
| GET | `/api/v1/encomiendas/pendientes/` | Solo pendientes |
| GET | `/api/v1/encomiendas/con_retraso/` | Encomiendas vencidas |
| GET | `/api/v1/encomiendas/estadisticas/` | Métricas (cacheado 15 min en Redis) |
| POST | `/api/v1/encomiendas/bulk_create/` | Crear varias a la vez |
| PATCH | `/api/v1/encomiendas/bulk_estado/` | Cambiar estado en lote |
| GET | `/api/v1/clientes/` | Clientes activos |
| GET | `/api/v1/rutas/` | Rutas disponibles |

### Filtros

```
/api/v1/encomiendas/?estado=PE
/api/v1/encomiendas/?search=Lima
/api/v1/encomiendas/?ordering=-fecha_registro
/api/v1/encomiendas/?desde=2026-01-01&hasta=2026-05-01
/api/v1/encomiendas/?con_retraso=true
```

### API v2

`/api/v2/encomiendas/` — versión de solo lectura con menos campos y un campo `resumen` con el estado en texto.

---

## Permisos y seguridad

- Solo usuarios con empleado activo en BD pueden usar la API (`EsEmpleadoActivo`)
- Empleados regulares solo modifican sus propias encomiendas (`EsPropietarioOAdmin`)
- Staff/admin tiene acceso completo
- Throttling: 100 req/hora por empleado, 5 intentos/min en login
- Campos sensibles (`empleado_registro`, `observaciones`) ocultos para no-staff

---

## Estructura

```
├── config/              # Settings, URLs, ASGI, choices globales
├── envios/              # App principal
│   ├── consumers.py     # WebSocket consumers (Dashboard, Encomienda, Feed)
│   ├── routing.py       # Rutas WebSocket
│   ├── async_services.py # Funciones de broadcast al Channel Layer
│   ├── viewsets.py      # API ViewSets con notificaciones WS integradas
│   └── management/commands/seed_data.py
├── clientes/
├── rutas/
├── api/                 # Filtros, paginación, permisos, throttles
│   └── v2/
├── templates/
├── static/
└── docker-compose.yml
```

---

## Tests

```bash
docker compose exec web python manage.py test envios.tests.test_api --verbosity=2
```

16 tests: listado, creación, validaciones, detalle anidado, cambio de estado, autenticación, filtros y estadísticas.

---

## Sesiones

| Sesión | Tema |
|--------|------|
| 03 | Modelos Django ORM, QuerySets, validadores |
| 04 | Autenticación, sesiones, vistas protegidas |
| 05 | Django REST Framework — serializers, JWT, Swagger |
| 06 | DRF avanzado — ViewSets, permisos, throttling, caché Redis, tests |
| 07 | Asincronía — WebSockets, Django Channels, Daphne, sistemas reactivos |
