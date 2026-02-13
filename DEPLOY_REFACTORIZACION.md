# 🚀 Guía de Despliegue - Aplicación Refactorizada

## 📋 Pre-requisitos

Asegúrate de tener todos los archivos nuevos:
- ✅ constants.py
- ✅ calculations.py
- ✅ analysis.py
- ✅ utils.py
- ✅ app.py (refactorizado - 4,915 líneas)
- ✅ Dockerfile (actualizado)

## 🔄 Pasos para Desplegar

### 1. Conectarse al Servidor

```powershell
ssh root@164.68.118.86
```

### 2. Ir al Directorio de la Aplicación

```bash
cd /opt/evaluaciones-rh
```

### 3. Hacer Backup de Producción Actual

```bash
# Backup del código actual
cp -r . ../evaluaciones-rh-backup-$(date +%Y%m%d_%H%M%S)

# Backup de la base de datos
cp data/evaluaciones_rh.db data/backup_$(date +%Y%m%d_%H%M%S).db
```

### 4. Subir Archivos Nuevos desde tu PC

Desde tu PC local (PowerShell):

```powershell
# Navegar a la carpeta del proyecto
cd "C:\Users\guiog\OneDrive\Documentos\RH test\disc-personality-assessment"

# Subir módulos nuevos
scp constants.py root@164.68.118.86:/opt/evaluaciones-rh/
scp calculations.py root@164.68.118.86:/opt/evaluaciones-rh/
scp analysis.py root@164.68.118.86:/opt/evaluaciones-rh/
scp utils.py root@164.68.118.86:/opt/evaluaciones-rh/

# Subir app.py refactorizado
scp app.py root@164.68.118.86:/opt/evaluaciones-rh/

# Subir Dockerfile actualizado
scp Dockerfile root@164.68.118.86:/opt/evaluaciones-rh/
```

### 5. Reconstruir y Desplegar

De vuelta en el servidor (SSH):

```bash
cd /opt/evaluaciones-rh

# Detener contenedor actual
docker-compose down

# Reconstruir imagen con archivos nuevos
docker-compose build --no-cache

# Iniciar con nueva versión
docker-compose up -d

# Ver logs para verificar
docker logs -f evaluaciones-rh-prod
```

## ✅ Verificación Post-Despliegue

### 1. Verificar que el contenedor está corriendo

```bash
docker ps | grep evaluaciones
```

Deberías ver:
```
CONTAINER ID   IMAGE           STATUS          PORTS
xxxxx          evaluaciones    Up X seconds    127.0.0.1:8505->8501/tcp
```

### 2. Verificar logs

```bash
docker logs --tail=50 evaluaciones-rh-prod
```

Deberías ver algo como:
```
You can now view your Streamlit app in your browser.
Network URL: http://0.0.0.0:8501
```

### 3. Probar la Aplicación

Desde tu navegador:
```
http://evaluaciones.164.68.118.86.nip.io/
```

### 4. Verificar Funcionalidad

- ✅ Página de inicio carga correctamente
- ✅ Login funciona
- ✅ Tests DISC funcionan
- ✅ Tests VALANTI funcionan
- ✅ Tests WPI funcionan
- ✅ Generación de PDF funciona
- ✅ Dashboard de administrador funciona

## 🔧 Troubleshooting

### Si el contenedor no inicia:

```bash
# Ver logs completos
docker logs evaluaciones-rh-prod

# Revisar errores de importación
docker exec -it evaluaciones-rh-prod python -c "import app; print('OK')"
```

### Si hay errores de importación:

```bash
# Verificar que los archivos están en el contenedor
docker exec -it evaluaciones-rh-prod ls -la /app/

# Debería mostrar:
# constants.py
# calculations.py
# analysis.py
# utils.py
# app.py
```

### Rollback si algo falla:

```bash
# Detener contenedor actual
docker-compose down

# Restaurar desde backup
cd /opt
mv evaluaciones-rh evaluaciones-rh-failed
mv evaluaciones-rh-backup-YYYYMMDD_HHMMSS evaluaciones-rh
cd evaluaciones-rh

# Reconstruir e iniciar
docker-compose build
docker-compose up -d
```

## 📊 Comparación de Tamaño

### Antes de la Refactorización:
- **app.py**: 6,765 líneas
- Módulos: 0
- Total archivos Python: 2 (app.py, database.py)

### Después de la Refactorización:
- **app.py**: 4,915 líneas (↓ 27%)
- **constants.py**: ~1,000 líneas
- **calculations.py**: ~400 líneas
- **analysis.py**: ~600 líneas
- **utils.py**: ~30 líneas
- Total archivos Python: 6

## 🎯 Ventajas del Nuevo Código

1. **Mejor organización**: Código modular y mantenible
2. **Menor tiempo de carga**: app.py 27% más pequeño
3. **Facilita actualizaciones**: Cambios en módulos específicos
4. **Mismo comportamiento**: 0 cambios en funcionalidad
5. **Backup disponible**: app_backup_original.py en caso de emergencia

## 📞 Soporte

Si tienes problemas:
1. Revisa los logs: `docker logs evaluaciones-rh-prod`
2. Verifica los archivos en el contenedor
3. Usa el backup si es necesario
4. Contacta al equipo de desarrollo

---

**Fecha de Despliegue**: 13 de febrero de 2026
**Versión**: 2.0 (Refactorizada)
**Estado**: ✅ Lista para Producción
