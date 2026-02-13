#!/bin/bash
# ====================================================
# Script de Verificación Post-Despliegue
# Ejecutar en el servidor después del despliegue
# ====================================================

echo ""
echo "=========================================="
echo "  VERIFICACIÓN POST-DESPLIEGUE"
echo "=========================================="
echo ""

# Colores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Función para verificar
check() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓${NC} $1"
        return 0
    else
        echo -e "${RED}✗${NC} $1"
        return 1
    fi
}

cd /opt/evaluaciones-rh

echo "[1/7] Verificando contenedor Docker..."
docker ps | grep evaluaciones-rh-prod > /dev/null
check "Contenedor está corriendo"
echo ""

echo "[2/7] Verificando archivos en el contenedor..."
docker exec evaluaciones-rh-prod ls -la /app/constants.py > /dev/null 2>&1
check "constants.py presente"
docker exec evaluaciones-rh-prod ls -la /app/calculations.py > /dev/null 2>&1
check "calculations.py presente"
docker exec evaluaciones-rh-prod ls -la /app/analysis.py > /dev/null 2>&1
check "analysis.py presente"
docker exec evaluaciones-rh-prod ls -la /app/utils.py > /dev/null 2>&1
check "utils.py presente"
docker exec evaluaciones-rh-prod ls -la /app/app.py > /dev/null 2>&1
check "app.py presente"
echo ""

echo "[3/7] Verificando importaciones Python..."
docker exec evaluaciones-rh-prod python -c "import constants; print('OK')" > /dev/null 2>&1
check "constants.py importa correctamente"
docker exec evaluaciones-rh-prod python -c "import calculations; print('OK')" > /dev/null 2>&1
check "calculations.py importa correctamente"
docker exec evaluaciones-rh-prod python -c "import analysis; print('OK')" > /dev/null 2>&1
check "analysis.py importa correctamente"
docker exec evaluaciones-rh-prod python -c "import utils; print('OK')" > /dev/null 2>&1
check "utils.py importa correctamente"
echo ""

echo "[4/7] Verificando que app.py puede importar todos los módulos..."
docker exec evaluaciones-rh-prod python -c "from constants import VALANTI_PREGUNTAS; from calculations import calculate_disc_results; from analysis import analyze_disc_aptitude; print('OK')" > /dev/null 2>&1
check "Todas las importaciones de app.py funcionan"
echo ""

echo "[5/7] Verificando puerto y servicio Streamlit..."
docker exec evaluaciones-rh-prod curl -s http://localhost:8501/_stcore/health > /dev/null 2>&1
check "Streamlit responde en puerto 8501"
echo ""

echo "[6/7] Verificando mapeo de puertos..."
netstat -tuln | grep 8505 > /dev/null 2>&1
check "Puerto 8505 está en escucha"
echo ""

echo "[7/7] Verificando logs (últimas 10 líneas)..."
echo -e "${YELLOW}Logs recientes:${NC}"
docker logs --tail=10 evaluaciones-rh-prod
echo ""

echo "=========================================="
echo "  RESUMEN DE VERIFICACIÓN"
echo "=========================================="
echo ""
echo -e "${GREEN}URL de acceso:${NC}"
echo "http://evaluaciones.164.68.118.86.nip.io/"
echo ""

echo -e "${GREEN}Comandos útiles:${NC}"
echo "Ver logs: docker logs -f evaluaciones-rh-prod"
echo "Reiniciar: docker-compose restart"
echo "Estado: docker ps | grep evaluaciones"
echo ""

# Test final HTTP
echo "Realizando test HTTP..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8505)
if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✓${NC} Aplicación respondió con HTTP $HTTP_CODE"
    echo ""
    echo -e "${GREEN}✓✓✓ DESPLIEGUE EXITOSO ✓✓✓${NC}"
else
    echo -e "${RED}✗${NC} Aplicación respondió con HTTP $HTTP_CODE"
    echo -e "${RED}Revisar logs para más detalles${NC}"
fi

echo ""
