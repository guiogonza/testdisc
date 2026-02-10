@echo off
REM Script de verificacion rapida del estado del servidor

echo ========================================
echo Verificacion de Estado - Servidor Produccion
echo ========================================
echo.

set SERVIDOR=root@164.68.118.86
set URL=http://164.68.118.86:8503

echo [*] Verificando conexion SSH...
ssh -o ConnectTimeout=5 %SERVIDOR% "echo OK" >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] SSH conectado
) else (
    echo [ERROR] No se puede conectar por SSH
)

echo.
echo [*] Verificando estado del contenedor...
ssh %SERVIDOR% "docker ps --filter name=evaluaciones-rh-prod --format '{{.Status}}'"

echo.
echo [*] Verificando puerto 8503...
ssh %SERVIDOR% "ss -tuln | grep 8503 && echo [OK] Puerto escuchando || echo [ERROR] Puerto no disponible"

echo.
echo [*] Verificando respuesta HTTP...
powershell -Command "try { $response = Invoke-WebRequest -Uri '%URL%' -UseBasicParsing -TimeoutSec 5; Write-Host '[OK] HTTP' $response.StatusCode } catch { Write-Host '[ERROR] No responde' }"

echo.
echo [*] Ultimos logs (5 lineas)...
ssh %SERVIDOR% "docker logs --tail 5 evaluaciones-rh-prod 2>&1"

echo.
echo [*] Uso de recursos del contenedor...
ssh %SERVIDOR% "docker stats evaluaciones-rh-prod --no-stream --format 'CPU: {{.CPUPerc}} | Memoria: {{.MemUsage}}'"

echo.
echo [*] Espacio en disco...
ssh %SERVIDOR% "df -h /opt/evaluaciones-rh | tail -1"

echo.
echo [*] Tamaño de base de datos...
ssh %SERVIDOR% "ls -lh /opt/evaluaciones-rh/data/evaluaciones_rh.db 2>/dev/null || echo 'Base de datos no encontrada'"

echo.
echo ========================================
echo Verificacion completada
echo ========================================
echo.
echo URL Aplicacion: %URL%
echo Usuario Admin: admin
echo.
pause
