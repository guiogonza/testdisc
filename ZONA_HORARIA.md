# Configuración de Zona Horaria — GMT-5 (Colombia)

## Problema
El servidor VPS está en Alemania (UTC+2). Sin configuración explícita, el contenedor Docker heredaba esa zona horaria, causando que los timestamps se mostraran desfasados en la interfaz.

## Solución aplicada

### 1. Variable de entorno en Docker (`docker-compose.prod.yml`)
```yaml
environment:
  - TZ=America/Bogota
```
Esto hace que el OS del contenedor opere en GMT-5, independientemente de la zona horaria del servidor host.

### 2. Python — `app.py` y `database.py`
Toda llamada a `datetime.now()` usa timezone explícita:
```python
from datetime import datetime, timedelta, timezone
_GMT5 = timezone(timedelta(hours=-5))
def _now_gmt5(): return datetime.now(_GMT5)
```
Esto garantiza GMT-5 **sin depender del OS**.

### 3. SQLite — DEFAULT en columnas `created_at`
```sql
created_at TEXT DEFAULT (datetime('now', '-5 hours'))
```
SQLite siempre trabaja en UTC internamente; se resta 5 horas en el DEFAULT.

---

## Corrección de datos históricos (23/04/2026)
Los `created_at` anteriores al fix estaban guardados en UTC puro. Se corrigieron restando 5 horas:
```sql
UPDATE test_sessions
SET created_at = datetime(created_at, '-5 hours')
WHERE created_at IS NOT NULL;
```
Los campos `started_at` y `completed_at` ya estaban correctos (los setea Python con `_now_gmt5()`).

---

## Flujo de despliegue de zona horaria

```powershell
# 1. Subir docker-compose actualizado
scp -i C:\Users\guiog\.ssh\id_rsa docker-compose.prod.yml root@164.68.118.86:/opt/evaluaciones-rh/

# 2. Recrear el contenedor (stop → rm → up)
ssh -i C:\Users\guiog\.ssh\id_rsa root@164.68.118.86 "docker stop evaluaciones-rh-prod; docker rm evaluaciones-rh-prod; cd /opt/evaluaciones-rh && docker-compose -f docker-compose.prod.yml up -d"

# 3. Copiar app.py dentro del nuevo contenedor
ssh -i C:\Users\guiog\.ssh\id_rsa root@164.68.118.86 "docker cp /opt/evaluaciones-rh/app.py evaluaciones-rh-prod:/app/app.py && docker restart evaluaciones-rh-prod"

# 4. Verificar hora en el contenedor
ssh -i C:\Users\guiog\.ssh\id_rsa root@164.68.118.86 "docker exec evaluaciones-rh-prod date"
# Debe mostrar -05 al final
```

> **NOTA:** Al recrear el contenedor, `app.py` vuelve al de la imagen base. Siempre ejecutar el paso 3 después de recrear.
