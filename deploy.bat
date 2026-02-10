@echo off
REM Script de despliegue rapido al servidor de produccion
REM Servidor: 164.68.118.86:8503

echo ========================================
echo Despliegue Rapido - Servidor Produccion
echo ========================================
echo.

REM Variables
set SERVIDOR=root@164.68.118.86
set DIRECTORIO=/opt/evaluaciones-rh

echo [1/5] Verificando conexion SSH...
ssh -o ConnectTimeout=5 %SERVIDOR% "echo Conexion OK" >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] No se puede conectar al servidor
    pause
    exit /b 1
)
echo [OK] Conexion SSH establecida

echo.
echo [2/5] Copiando archivos al servidor...
scp app.py valanti_app.py disc_style.py database.py requirements.txt Dockerfile .dockerignore ^
    questions_es.json questions.json ^
    disc_descriptions_es.json disc_descriptions.json ^
    streangths.json ^
    docker-compose.prod.yml ^
    %SERVIDOR%:%DIRECTORIO%/

if %errorlevel% neq 0 (
    echo [ERROR] Fallo al copiar archivos
    pause
    exit /b 1
)
echo [OK] Archivos copiados

echo.
echo [3/5] Preparando entorno en servidor...
ssh %SERVIDOR% "cd %DIRECTORIO% && mv docker-compose.prod.yml docker-compose.yml 2>/dev/null || true && mkdir -p data"
echo [OK] Entorno preparado

echo.
echo [4/5] Deteniendo contenedor anterior...
ssh %SERVIDOR% "cd %DIRECTORIO% && docker-compose down"
echo [OK] Contenedor detenido

echo.
echo [5/5] Construyendo y desplegando nueva version...
ssh %SERVIDOR% "cd %DIRECTORIO% && docker-compose build --no-cache && docker-compose up -d"

if %errorlevel% neq 0 (
    echo [ERROR] Fallo al desplegar
    pause
    exit /b 1
)

echo.
echo ========================================
echo [EXITO] Despliegue completado
echo ========================================
echo.
echo URL: http://164.68.118.86:8503
echo Usuario: admin
echo Password: admin123
echo.
echo Verificando estado...
timeout /t 3 /nobreak >nul

ssh %SERVIDOR% "docker ps | grep evaluaciones"
echo.

echo Presiona cualquier tecla para ver logs...
pause >nul

ssh %SERVIDOR% "docker logs --tail 30 evaluaciones-rh-prod"
