# 🐳 Guía de Despliegue Docker

## Inicio Rápido

```bash
# 1. Construir e iniciar
docker-compose up -d

# 2. Acceder a la aplicación
# http://localhost:8501

# 3. Login administrador
# Usuario: admin
# Contraseña: admin123
```

## Comandos Útiles

### Gestión del Contenedor

```bash
# Ver logs en tiempo real
docker-compose logs -f

# Reiniciar aplicación
docker-compose restart

# Detener todo
docker-compose down

# Reconstruir imagen (después de cambios)
docker-compose build --no-cache
docker-compose up -d
```

### Monitoreo

```bash
# Estado del contenedor
docker-compose ps

# Uso de recursos
docker stats evaluaciones-rh-app

# Inspeccionar salud del contenedor
docker inspect evaluaciones-rh-app | grep -A 10 Health
```

## Persistencia de Datos

### Ubicación de la Base de Datos

- **Local**: `./data/evaluaciones_rh.db`
- **Contenedor**: `/app/data/evaluaciones_rh.db`

El volumen Docker mapea ambas rutas automáticamente.

### Backup de Datos

```bash
# Backup manual
docker-compose exec evaluaciones-rh cp /app/data/evaluaciones_rh.db /app/data/backup_$(date +%Y%m%d_%H%M%S).db

# O desde el host
cp data/evaluaciones_rh.db backup_$(date +%Y%m%d_%H%M%S).db
```

### Restaurar Backup

```bash
# Detener contenedor
docker-compose down

# Restaurar archivo
cp backup_YYYYMMDD.db data/evaluaciones_rh.db

# Reiniciar
docker-compose up -d
```

## Configuración Avanzada

### Cambiar Puerto

Editar `docker-compose.yml`:

```yaml
ports:
  - "8080:8501"  # La app estará en localhost:8080
```

### Variables de Entorno

Agregar en `docker-compose.yml`:

```yaml
environment:
  - STREAMLIT_THEME_BASE=light
  - STREAMLIT_THEME_PRIMARY_COLOR=#FF4B4B
  - STREAMLIT_SERVER_MAX_UPLOAD_SIZE=200
```

### Límites de Recursos

```yaml
services:
  evaluaciones-rh:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 512M
```

## Troubleshooting

### Error: Puerto 8501 ocupado

```bash
# Opción 1: Liberar puerto
netstat -ano | findstr :8501
taskkill /PID <PID> /F

# Opción 2: Cambiar puerto en docker-compose.yml
ports:
  - "8502:8501"
```

### Error: Imagen no construye

```bash
# Limpiar cache de Docker
docker system prune -a

# Reconstruir desde cero
docker-compose build --no-cache
```

### Error: Base de datos corrupta

```bash
# Detener contenedor
docker-compose down

# Respaldar BD corrupta
mv data/evaluaciones_rh.db data/evaluaciones_rh.db.corrupted

# Reiniciar (crea nueva BD)
docker-compose up -d
```

### Contenedor se detiene inmediatamente

```bash
# Ver logs de error
docker-compose logs evaluaciones-rh

# Ejecutar en primer plano para debug
docker-compose up
```

## Producción

### Configuración Recomendada

```yaml
version: '3.8'

services:
  evaluaciones-rh:
    build: .
    container_name: evaluaciones-rh-prod
    ports:
      - "80:8501"
    volumes:
      - /ruta/produccion/data:/app/data
    environment:
      - STREAMLIT_SERVER_HEADLESS=true
      - STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
    restart: always
    deploy:
      resources:
        limits:
          memory: 2G
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8501/_stcore/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### Reverse Proxy con Nginx

```nginx
server {
    listen 80;
    server_name evaluaciones.empresa.com;

    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```

## Actualización de Versión

```bash
# 1. Detener contenedor
docker-compose down

# 2. Hacer backup de datos
cp -r data data_backup_$(date +%Y%m%d)

# 3. Actualizar código (git pull, etc.)

# 4. Reconstruir imagen
docker-compose build

# 5. Iniciar nueva versión
docker-compose up -d

# 6. Verificar logs
docker-compose logs -f
```

## Desinstalación

```bash
# Detener y eliminar contenedor
docker-compose down

# Eliminar imagen
docker rmi evaluaciones-rh

# Eliminar volumen de datos (CUIDADO: elimina toda la información)
rm -rf data/
```

## Soporte

Para problemas técnicos, revisar:
1. Logs del contenedor: `docker-compose logs -f`
2. Estado de salud: `docker-compose ps`
3. Conectividad: `docker exec evaluaciones-rh-app curl http://localhost:8501/_stcore/health`
