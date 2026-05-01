# 📦 Sistema de Gestión de Encomiendas

Proyecto académico desarrollado con **Django + Docker + PostgreSQL**.  
Implementa un sistema completo de gestión de encomiendas con autenticación, dashboard, formularios validados y panel de administración.

---

## 🛠️ Tecnologías

- Python 3.11 + Django 4.x
- PostgreSQL 15
- Docker + Docker Compose
- Bootstrap 5 + Bootstrap Icons
- Google Fonts (Inter)

---

## 1. Instalar Docker en Linux Mint / Ubuntu

```bash
sudo apt-get update
sudo apt-get install ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc

echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$UBUNTU_CODENAME") stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt-get update
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo usermod -aG docker $USER
newgrp docker
```

Verificar la instalación:

```bash
docker --version
docker compose version
docker run hello-world
```

---

## 2. Ejecutar el proyecto

### Clonar el repositorio

```bash
git clone https://github.com/SleyterCorrea/encomiendas-django-docker.git
cd encomiendas-django-docker
```

### Configurar variables de entorno

```bash
cp .env.example .env
```

> ⚠️ Edita el `.env` si necesitas cambiar la base de datos o la SECRET_KEY.

### Levantar los contenedores

```bash
docker compose up --build -d
```

> **Nota:** Si el puerto `8001` o `5433` ya están en uso en tu máquina, edita el `docker-compose.yml` y cámbialos por otros libres.

### Aplicar migraciones

```bash
docker compose exec web python manage.py migrate
```

### Crear superusuario (acceso al admin y al sistema)

```bash
docker compose exec web python manage.py createsuperuser
```

### Abrir en el navegador

| Servicio | URL |
|---|---|
| 🖥️ Sistema (login/dashboard) | http://localhost:8001 |
| ⚙️ Panel de administración | http://localhost:8001/admin |
| 🗄️ pgAdmin (gestor de BD) | http://localhost:5050 |

> El sistema redirige automáticamente a `/accounts/login/` si no estás autenticado.

---

## 3. Estructura del proyecto

```
encomiendas/
├── config/          ← settings, urls, choices
├── envios/          ← modelos, vistas, formularios, admin, urls
├── clientes/        ← modelo Cliente
├── rutas/           ← modelo Ruta
├── templates/       ← base.html, navbar, dashboard, lista, detalle, form, login
├── static/          ← css/styles.css, js/main.js
├── Dockerfile
├── docker-compose.yml
└── .env.example
```

---

## 4. Funcionalidades implementadas

- ✅ Dashboard con contadores: activas, en tránsito, con retraso
- ✅ Lista paginada (15/pág) con filtro por estado
- ✅ Detalle de encomienda con historial de cambios de estado
- ✅ Formulario de nueva encomienda con validación client-side y server-side
- ✅ `EncomiendaForm` filtra solo clientes y rutas activos
- ✅ Mensajes flash de éxito/error en operaciones CRUD
- ✅ `EncomiendaAdmin` con badges de color por estado y fieldsets
- ✅ Título del admin personalizado: "Sistema de Encomiendas"
- ✅ Login y logout con `@login_required` en todas las vistas
- ✅ Navbar con usuario logueado y botón de cerrar sesión

---

## 5. Comandos útiles

```bash
# Ver logs en tiempo real
docker compose logs -f web
docker compose logs -f db

# Detener los contenedores
docker compose down

# Detener y eliminar volúmenes (borra la BD)
docker compose down -v

# Abrir shell de Django
docker compose exec web python manage.py shell

# Recolectar archivos estáticos
docker compose exec web python manage.py collectstatic
```

---

## 6. Subir cambios a GitHub

```bash
git add .
git commit -m "descripción del cambio"
git push origin main
```
