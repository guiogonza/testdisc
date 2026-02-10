@echo off
REM Script de inicio para la plataforma de evaluaciones RH

echo ========================================
echo Plataforma de Evaluaciones Psicometricas
echo ========================================
echo.

REM Verificar si Docker esta instalado
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Docker no esta instalado
    echo Descargalo desde: https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)

REM Verificar si docker-compose esta instalado
docker-compose --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: docker-compose no esta instalado
    pause
    exit /b 1
)

echo [OK] Docker instalado correctamente
echo.

REM Crear directorio data si no existe
if not exist "data" (
    echo Creando directorio de datos...
    mkdir data
)

echo.
echo Opciones:
echo 1. Iniciar aplicacion (Docker)
echo 2. Detener aplicacion
echo 3. Ver logs
echo 4. Reiniciar aplicacion
echo 5. Reconstruir imagen
echo 6. Backup de base de datos
echo 7. Iniciar en modo desarrollo (sin Docker)
echo 8. Salir
echo.

set /p choice="Selecciona una opcion (1-8): "

if "%choice%"=="1" goto start
if "%choice%"=="2" goto stop
if "%choice%"=="3" goto logs
if "%choice%"=="4" goto restart
if "%choice%"=="5" goto rebuild
if "%choice%"=="6" goto backup
if "%choice%"=="7" goto dev
if "%choice%"=="8" goto end
goto menu

:start
echo.
echo Iniciando aplicacion...
docker-compose up -d
if %errorlevel% equ 0 (
    echo.
    echo [OK] Aplicacion iniciada correctamente
    echo Accede en: http://localhost:8501
    echo.
    echo Usuario: admin
    echo Contrasena: admin123
) else (
    echo [ERROR] Fallo al iniciar la aplicacion
)
pause
goto end

:stop
echo.
echo Deteniendo aplicacion...
docker-compose down
echo [OK] Aplicacion detenida
pause
goto end

:logs
echo.
echo Mostrando logs (Ctrl+C para salir)...
docker-compose logs -f
goto end

:restart
echo.
echo Reiniciando aplicacion...
docker-compose restart
echo [OK] Aplicacion reiniciada
pause
goto end

:rebuild
echo.
echo Reconstruyendo imagen...
docker-compose down
docker-compose build --no-cache
docker-compose up -d
echo [OK] Imagen reconstruida e iniciada
pause
goto end

:backup
echo.
echo Creando backup de base de datos...
set timestamp=%date:~-4%%date:~3,2%%date:~0,2%_%time:~0,2%%time:~3,2%%time:~6,2%
set timestamp=%timestamp: =0%
if exist "data\evaluaciones_rh.db" (
    copy "data\evaluaciones_rh.db" "data\backup_%timestamp%.db"
    echo [OK] Backup creado: backup_%timestamp%.db
) else (
    echo [AVISO] No se encontro base de datos para respaldar
)
pause
goto end

:dev
echo.
echo Iniciando en modo desarrollo...
echo.
echo Verificando dependencias...
pip install -r requirements.txt
echo.
echo Iniciando Streamlit...
streamlit run app.py
goto end

:end
echo.
echo Gracias por usar la plataforma de evaluaciones RH
