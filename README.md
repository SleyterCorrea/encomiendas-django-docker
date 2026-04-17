# Sistema de Gestión de Encomiendas

Proyecto base en **Django + Docker + PostgreSQL**, preparado para **Linux Mint** siguiendo la estructura de las diapositivas.

## 1. Instalar Docker en Linux Mint

```bash
sudo apt-get update
sudo apt-get install ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc

echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo \"$UBUNTU_CODENAME\") stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt-get update
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo usermod -aG docker $USER
newgrp docker
```

Verificar:

```bash
docker --version
docker compose version
docker run hello-world
```

## 2. Ejecutar el proyecto

Clona el repositorio o descomprime este proyecto:

```bash
cp .env.example .env
```

Luego levanta los contenedores:

```bash
docker compose up --build -d
```

Aplica migraciones:

```bash
docker compose exec web python manage.py makemigrations clientes rutas envios
docker compose exec web python manage.py migrate
```

Crea superusuario:

```bash
docker compose exec web python manage.py createsuperuser
```

Abrir en navegador:

- App: http://localhost:8000
- Admin: http://localhost:8000/admin

## 3. Apps incluidas

- `envios`
- `clientes`
- `rutas`

## 4. Subir a GitHub

```bash
git init
git add .
git commit -m "Proyecto Django con Docker"
git branch -M main
git remote add origin https://github.com/TU_USUARIO/TU_REPO.git
git push -u origin main
```

## 5. Comandos útiles

```bash
docker compose logs -f web
docker compose logs -f db
docker compose down
docker compose down -v
```
