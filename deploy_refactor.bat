@echo off
REM ====================================================
REM Script de Despliegue de Aplicación Refactorizada
REM ====================================================

echo.
echo ========================================
echo   DESPLIEGUE - APLICACION REFACTORIZADA
echo ========================================
echo.

REM Servidor de producción
set SERVER=root@164.68.118.86
set REMOTE_PATH=/opt/evaluaciones-rh

echo [1/6] Verificando archivos locales...
if not exist "constants.py" (
    echo ERROR: constants.py no encontrado
    pause
    exit /b 1
)
if not exist "calculations.py" (
    echo ERROR: calculations.py no encontrado
    pause
    exit /b 1
)
if not exist "analysis.py" (
    echo ERROR: analysis.py no encontrado
    pause
    exit /b 1
)
if not exist "utils.py" (
    echo ERROR: utils.py no encontrado
    pause
    exit /b 1
)
echo OK - Todos los archivos presentes
echo.

echo [2/6] Subiendo modulos nuevos al servidor...
scp constants.py %SERVER%:%REMOTE_PATH%/
scp calculations.py %SERVER%:%REMOTE_PATH%/
scp analysis.py %SERVER%:%REMOTE_PATH%/
scp utils.py %SERVER%:%REMOTE_PATH%/
echo.

echo [3/6] Subiendo app.py refactorizado...
scp app.py %SERVER%:%REMOTE_PATH%/
echo.

echo [4/6] Subiendo Dockerfile actualizado...
scp Dockerfile %SERVER%:%REMOTE_PATH%/
echo.

echo [5/6] Ejecutando reconstruccion en el servidor...
echo (Esto puede tomar 2-3 minutos)
ssh %SERVER% "cd %REMOTE_PATH% && docker-compose down && docker-compose build --no-cache && docker-compose up -d"
echo.

echo [6/6] Esperando que el servicio inicie (30 segundos)...
timeout /t 30 /nobreak > nul
echo.

echo ========================================
echo   DESPLIEGUE COMPLETADO
echo ========================================
echo.
echo URL: http://evaluaciones.164.68.118.86.nip.io/
echo.
echo Verificando estado del servicio...
ssh %SERVER% "docker ps | grep evaluaciones"
echo.

echo Para ver los logs en tiempo real:
echo ssh %SERVER% "docker logs -f evaluaciones-rh-prod"
echo.

pause
