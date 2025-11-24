#!/bin/bash
# Ejemplos de uso de la API de consulta de deudas

# Configuración
API_URL="http://localhost:8000"

echo "==================================="
echo "  EJEMPLOS DE USO DE LA API"
echo "==================================="
echo ""

# 1. Health check
echo "1️⃣  Health Check"
echo "$ curl $API_URL/health"
curl -s $API_URL/health | jq .
echo ""
echo ""

# 2. Root endpoint (lista de endpoints)
echo "2️⃣  Endpoints disponibles"
echo "$ curl $API_URL/"
curl -s $API_URL/ | jq .
echo ""
echo ""

# 3. Listar servicios de una propiedad
echo "3️⃣  Listar servicios de propiedad 35"
echo "$ curl $API_URL/servicios/propiedad/35"
curl -s $API_URL/servicios/propiedad/35 | jq .
echo ""
echo ""

# 4. Consultar deudas de una propiedad
echo "4️⃣  Consultar deudas de propiedad 35 (esto tomará unos minutos)"
echo "$ curl -X POST $API_URL/consultar/propiedad -H 'Content-Type: application/json' -d '{\"propiedad_id\": 35}'"
echo ""
echo "⚠️  Este comando hará consultas reales y consumirá créditos"
echo "⚠️  Descomenta la siguiente línea para ejecutar:"
echo ""
# curl -X POST $API_URL/consultar/propiedad -H "Content-Type: application/json" -d '{"propiedad_id": 35}' | jq .
echo ""

# 5. Ver historial de consultas
echo "5️⃣  Ver historial de consultas de propiedad 35"
echo "$ curl $API_URL/historial/propiedad/35"
curl -s $API_URL/historial/propiedad/35 | jq .
echo ""
echo ""

# 6. Consultar servicios específicos
echo "6️⃣  Consultar servicios específicos (IDs: 1, 3)"
echo "$ curl -X POST $API_URL/consultar/servicios -H 'Content-Type: application/json' -d '{\"servicio_ids\": [1, 3]}'"
echo ""
echo "⚠️  Descomenta para ejecutar:"
# curl -X POST $API_URL/consultar/servicios -H "Content-Type: application/json" -d '{"servicio_ids": [1, 3]}' | jq .
echo ""

# 7. Consultar todas las propiedades (background)
echo "7️⃣  Consultar TODAS las propiedades (en background)"
echo "$ curl -X POST $API_URL/consultar/todas"
echo ""
echo "⚠️  Descomenta para ejecutar (procesará TODOS los servicios):"
# curl -X POST $API_URL/consultar/todas | jq .
echo ""

echo "==================================="
echo "  FIN DE EJEMPLOS"
echo "==================================="
echo ""
echo "💡 Tips:"
echo "   • Instala 'jq' para formatear JSON: brew install jq"
echo "   • La API debe estar corriendo: uv run python api.py"
echo "   • Los endpoints de consulta real están comentados para evitar consumo accidental"
