# 🚀 Despliegue Exitoso - Servidor Producción

## ✅ Estado de Despliegue

**Servidor**: 164.68.118.86 (Contabo VPS - Ubuntu)  
**Puerto**: 8503  
**Contenedor**: evaluaciones-rh-prod  
**Estado**: ✅ Running (HTTP 200 OK)

---

## 🌐 Acceso a la Aplicación

### URL Pública
```
http://164.68.118.86:8503
```

### Credenciales Administrador
- **Usuario**: `admin`
- **Contraseña**: `admin123`

⚠️ **IMPORTANTE**: Cambiar la contraseña después del primer login (pestaña Configuración).

---

## 📊 Información del Servidor

**Sistema Operativo**: Linux Ubuntu 5.4.0-216-generic  
**Docker**: 28.1.1  
**Python**: 3.11-slim  
**Ubicación**: `/opt/evaluaciones-rh`

### Puertos Ocupados en el Servidor
- 22 (SSH)
- 80 (HTTP)
- 443 (HTTPS)
- 8501, 8502 (Otros servicios Streamlit)
- **8503** ← Tu aplicación de evaluaciones RH

---

## 🔧 Gestión Remota (SSH)

### Conectarse al Servidor
```powershell
ssh root@164.68.118.86
```

### Comandos Útiles

#### Ver estado del contenedor
```bash
cd /opt/evaluaciones-rh
docker ps | grep evaluaciones
```

#### Ver logs en tiempo real
```bash
docker logs -f evaluaciones-rh-prod
```

#### Reiniciar aplicación
```bash
docker-compose restart
```

#### Detener aplicación
```bash
docker-compose down
```

#### Iniciar aplicación
```bash
docker-compose up -d
```

#### Reconstruir después de cambios
```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

#### Backup de base de datos
```bash
cd /opt/evaluaciones-rh
cp data/evaluaciones_rh.db data/backup_$(date +%Y%m%d_%H%M%S).db
```

#### Descargar backup a PC local
```powershell
scp root@164.68.118.86:/opt/evaluaciones-rh/data/evaluaciones_rh.db ./backup_produccion.db
```

---

## 📦 Actualizar la Aplicación

### Desde tu PC local

```powershell
# 1. Navegar al directorio del proyecto
cd "C:\Users\guiog\OneDrive\Documentos\Disc RH\disc-personality-assessment"

# 2. Hacer cambios en app.py, database.py, etc.

# 3. Copiar archivos actualizados al servidor
scp app.py database.py requirements.txt root@164.68.118.86:/opt/evaluaciones-rh/

# 4. Reconstruir y reiniciar en el servidor
ssh root@164.68.118.86 'cd /opt/evaluaciones-rh && docker-compose down && docker-compose build --no-cache && docker-compose up -d'

# 5. Verificar logs
ssh root@164.68.118.86 'docker logs -f evaluaciones-rh-prod'
```

---

## 🔍 Monitoreo

### Verificar salud de la aplicación
```bash
curl -I http://164.68.118.86:8503
# Debe retornar: HTTP/1.1 200 OK
```

### Ver uso de recursos
```bash
docker stats evaluaciones-rh-prod
```

### Inspeccionar contenedor
```bash
docker inspect evaluaciones-rh-prod
```

---

## 🛡️ Seguridad

### Recomendaciones Inmediatas
1. ✅ Cambiar contraseña de admin al primer login
2. ⚠️ Configurar firewall si necesario (actualmente puerto 8503 abierto)
3. ⚠️ Considerar nginx reverse proxy con SSL/HTTPS
4. ✅ Base de datos protegida en volumen Docker

### Configurar HTTPS (Opcional con Nginx)
```bash
# Instalar nginx
apt update && apt install nginx certbot python3-certbot-nginx

# Crear configuración nginx
nano /etc/nginx/sites-available/evaluaciones

# Contenido:
server {
    listen 80;
    server_name evaluaciones.tudominio.com;
    
    location / {
        proxy_pass http://localhost:8503;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}

# Activar sitio
ln -s /etc/nginx/sites-available/evaluaciones /etc/nginx/sites-enabled/
nginx -t
systemctl restart nginx

# Obtener certificado SSL
certbot --nginx -d evaluaciones.tudominio.com
```

---

## 📋 Arquitectura del Despliegue

```
┌─────────────────────────────────────────┐
│  Internet (Puerto 8503)                 │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│  Servidor Ubuntu (164.68.118.86)        │
│  ┌─────────────────────────────────┐    │
│  │  Docker Container               │    │
│  │  evaluaciones-rh-prod           │    │
│  │  ┌──────────────────────────┐   │    │
│  │  │  Streamlit App           │   │    │
│  │  │  Puerto 8501 (interno)   │   │    │
│  │  │  → 8503 (externo)        │   │    │
│  │  └──────────────────────────┘   │    │
│  │                                  │    │
│  │  Volumen: /opt/evaluaciones-rh/ │    │
│  │           data/                  │    │
│  │           ├─ evaluaciones_rh.db  │    │
│  │           └─ backups/            │    │
│  └─────────────────────────────────┘    │
└──────────────────────────────────────────┘
```

---

## 🎯 Próximos Pasos

1. ✅ Acceder a http://164.68.118.86:8503
2. ✅ Login como admin/admin123
3. ✅ Cambiar contraseña en pestaña Configuración
4. ✅ Crear primer candidato
5. ✅ Asignar evaluación DISC o VALANTI
6. ✅ Probar flujo completo

---

## 📞 Soporte Técnico

**Servidor**: root@164.68.118.86  
**Directorio**: /opt/evaluaciones-rh  
**Logs**: `docker logs evaluaciones-rh-prod`  
**Base de datos**: /opt/evaluaciones-rh/data/evaluaciones_rh.db

---

## 🗑️ Desinstalar Aplicación

```bash
# Conectar al servidor
ssh root@164.68.118.86

# Detener y eliminar contenedor
cd /opt/evaluaciones-rh
docker-compose down

# Backup antes de eliminar (opcional)
cp -r data /root/backup_evaluaciones_$(date +%Y%m%d)

# Eliminar imagen Docker
docker rmi evaluaciones-rh_evaluaciones-rh

# Eliminar directorio completo
cd /opt
rm -rf evaluaciones-rh
```

---

**Fecha de Despliegue**: 10 de Febrero de 2026  
**Versión**: 1.0.0  
**Desplegado por**: Automatización SSH
