#!/bin/bash

# Script de verificación rápida de la integración
# Uso: ./quick_test.sh

set -e

echo "🔍 Verificación Rápida de Integración Agente + Next.js"
echo "======================================================="
echo ""

# Colores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Variables
AGENT_URL="http://localhost:8000"
NEXTJS_URL="http://localhost:3000"
TEST_VOUCHER_ID="test-voucher-123"
TEST_PROPIEDAD_ID="35"

# Función para verificar servicio
check_service() {
    local url=$1
    local name=$2

    echo -n "Verificando $name... "
    if curl -s -f -o /dev/null "$url"; then
        echo -e "${GREEN}✓${NC}"
        return 0
    else
        echo -e "${RED}✗${NC}"
        return 1
    fi
}

# 1. Verificar Agente
echo "1️⃣  Verificando Agente"
if check_service "$AGENT_URL/health" "Agente"; then
    echo "   URL: $AGENT_URL"
else
    echo -e "   ${RED}ERROR: Agente no está corriendo${NC}"
    echo "   Ejecuta: python api.py"
    exit 1
fi
echo ""

# 2. Verificar Next.js
echo "2️⃣  Verificando Next.js"
if check_service "$NEXTJS_URL" "Next.js"; then
    echo "   URL: $NEXTJS_URL"
else
    echo -e "   ${YELLOW}WARNING: Next.js no está en localhost:3000${NC}"
    echo "   Si estás usando ngrok, esto es normal."
fi
echo ""

# 3. Verificar endpoint de callback
echo "3️⃣  Verificando endpoint de callback"
CALLBACK_URL="$NEXTJS_URL/api/vouchers/$TEST_VOUCHER_ID/servicios-basicos"

echo -n "   Probando POST al callback... "
RESPONSE=$(curl -s -w "%{http_code}" -X POST "$CALLBACK_URL" \
    -H "Content-Type: application/json" \
    -d '{"resultados":[]}' \
    -o /dev/null)

if [ "$RESPONSE" = "404" ]; then
    echo -e "${YELLOW}404${NC} (Voucher no existe - esperado para test)"
elif [ "$RESPONSE" = "200" ]; then
    echo -e "${GREEN}200${NC} (OK)"
else
    echo -e "${RED}$RESPONSE${NC} (Inesperado)"
fi
echo ""

# 4. Verificar estadísticas de la cola
echo "4️⃣  Verificando cola de trabajos"
STATS=$(curl -s "$AGENT_URL/queue/stats")
if [ $? -eq 0 ]; then
    echo "   Estadísticas:"
    echo "$STATS" | jq -r '"   Total jobs: \(.total_jobs)\n   Pending: \(.pending)\n   Processing: \(.processing)\n   Completed: \(.completed)\n   Failed: \(.failed)\n   Workers: \(.max_workers)"'
else
    echo -e "   ${RED}ERROR: No se pudo obtener estadísticas${NC}"
fi
echo ""

# 5. Sugerencias para el test
echo "5️⃣  Siguiente paso: Test end-to-end"
echo ""
echo "   Para hacer un test completo:"
echo ""
echo "   A) Con ngrok (recomendado):"
echo "      Terminal 1: pnpm dev"
echo "      Terminal 2: ngrok http 3000"
echo "      Terminal 3: Copiar URL de ngrok"
echo ""
echo "   B) Request de prueba:"
echo "      curl -X POST $AGENT_URL/consultar/propiedad \\"
echo "        -H 'Content-Type: application/json' \\"
echo "        -d '{"
echo "          \"propiedad_id\": $TEST_PROPIEDAD_ID,"
echo "          \"callback_url\": \"https://TU-NGROK-URL/api/vouchers/$TEST_VOUCHER_ID/servicios-basicos\""
echo "        }'"
echo ""
echo "   C) Monitorear:"
echo "      - Logs del agente (donde corre api.py)"
echo "      - Logs de ngrok"
echo "      - Logs de Next.js"
echo ""

# 6. Verificar archivos de documentación
echo "6️⃣  Documentación disponible"
DOC_FILES=(
    "INTEGRACION_COMPLETA.md"
    "CALLBACKS_GUIDE.md"
    "CHANGELOG_CALLBACKS.md"
    "RESPUESTAS_PARA_NEXTJS.md"
    "RESUMEN_INTEGRACION.md"
)

for file in "${DOC_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo -e "   ${GREEN}✓${NC} $file"
    else
        echo -e "   ${RED}✗${NC} $file (faltante)"
    fi
done
echo ""

# Resumen
echo "======================================================="
echo "✅ Verificación completada"
echo ""
echo "Si todos los checks pasaron, estás listo para hacer el test!"
echo "Consulta INTEGRACION_COMPLETA.md para instrucciones detalladas."
echo ""
