@echo off
REM ============================================================
REM  deploy_full.bat — Despliegue completo al servidor de prod
REM  Sube código Python, configs nginx y reconstruye Docker
REM ============================================================

echo.
echo ============================================================
echo   DESPLIEGUE COMPLETO — 164.68.118.86
echo ============================================================
echo.

set SERVER=root@164.68.118.86
set REMOTE_APP=/opt/evaluaciones-rh
set SSH_KEY=C:\Users\guiog\.ssh\id_ed25519

REM ── 1. Verificar conexión ────────────────────────────────────
echo [1/6] Verificando conexion SSH...
ssh -i %SSH_KEY% -o ConnectTimeout=8 -o BatchMode=yes %SERVER% "echo OK" >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] No se puede conectar al servidor. Verificar VPN/clave SSH.
    pause
    exit /b 1
)
echo       Conexion SSH OK
echo.

REM ── 2. Subir archivos Python ─────────────────────────────────
echo [2/6] Subiendo modulos Python...
scp -i %SSH_KEY% ^
    app.py ^
    calculations.py ^
    analysis.py ^
    utils.py ^
    constants.py ^
    database.py ^
    questions_es.json ^
    questions.json ^
    questions_eri.json ^
    questions_wpi.json ^
    questions_talent_map.json ^
    disc_descriptions_es.json ^
    disc_descriptions.json ^
    streangths.json ^
    requirements.txt ^
    Dockerfile ^
    %SERVER%:%REMOTE_APP%/
if %errorlevel% neq 0 (
    echo [ERROR] Fallo al copiar archivos Python
    pause
    exit /b 1
)
echo       Archivos Python subidos OK
echo.

REM ── 3. Subir docker-compose ──────────────────────────────────
echo [3/6] Subiendo docker-compose...
scp -i %SSH_KEY% docker-compose.prod.yml %SERVER%:%REMOTE_APP%/docker-compose.yml
if %errorlevel% neq 0 (
    echo [ERROR] Fallo al copiar docker-compose
    pause
    exit /b 1
)
echo       docker-compose subido OK
echo.

REM ── 4. Subir y activar configs nginx ─────────────────────────
echo [4/6] Subiendo configuraciones nginx...

REM Config para dominio nip.io (ya existente — HTTP plano)
scp -i %SSH_KEY% evaluaciones-plain-http.nginx ^
    %SERVER%:/etc/nginx/sites-available/evaluaciones-nipio.conf

REM Config NUEVA para IP con prefijo /evaluacionesrh
scp -i %SSH_KEY% evaluaciones-ip.nginx ^
    %SERVER%:/etc/nginx/sites-available/evaluaciones-ip.conf

if %errorlevel% neq 0 (
    echo [ERROR] Fallo al copiar configs nginx
    pause
    exit /b 1
)

REM Crear symlinks en sites-enabled y recargar nginx
ssh -i %SSH_KEY% %SERVER% "^
    ln -sf /etc/nginx/sites-available/evaluaciones-nipio.conf /etc/nginx/sites-enabled/evaluaciones-nipio.conf && ^
    ln -sf /etc/nginx/sites-available/evaluaciones-ip.conf    /etc/nginx/sites-enabled/evaluaciones-ip.conf && ^
    nginx -t && systemctl reload nginx ^
"
if %errorlevel% neq 0 (
    echo [ERROR] Fallo al activar/recargar nginx
    pause
    exit /b 1
)
echo       Nginx recargado OK
echo.

REM ── 5. Reconstruir contenedor Docker ─────────────────────────
echo [5/6] Reconstruyendo contenedor Docker...
echo       (puede tardar 2-4 minutos)
ssh -i %SSH_KEY% %SERVER% "^
    cd %REMOTE_APP% && ^
    docker-compose down && ^
    docker-compose build --no-cache && ^
    docker-compose up -d ^
"
if %errorlevel% neq 0 (
    echo [ERROR] Fallo al reconstruir el contenedor
    pause
    exit /b 1
)
echo       Contenedor reconstruido OK
echo.

REM ── 6. Verificar ─────────────────────────────────────────────
echo [6/6] Esperando inicio del servicio (35 segundos)...
timeout /t 35 /nobreak > nul

echo.
echo Verificando estado del contenedor...
ssh -i %SSH_KEY% %SERVER% "docker ps | grep evaluaciones-rh"

echo.
echo Probando health-check interno...
ssh -i %SSH_KEY% %SERVER% "curl -s -o /dev/null -w '%%{http_code}' http://127.0.0.1:8505/_stcore/health"
echo.

echo.
echo ============================================================
echo   DESPLIEGUE COMPLETADO
echo ============================================================
echo.
echo   Subdominio:  http://evaluaciones.164.68.118.86.nip.io/
echo   Por IP/ruta: http://164.68.118.86/evaluacionesrh
echo.
echo   Logs en tiempo real:
echo   ssh -i %SSH_KEY% %SERVER% "docker logs -f evaluaciones-rh-prod"
echo.
pause
