# Guía de Integración Completa - Agente + Next.js

## 🎯 Objetivo

Esta guía detalla cómo integrar el agente de servicios básicos con la aplicación Next.js para automatizar la consulta de deudas en vouchers.

---

## 📊 Flujo Completo del Sistema

```
┌─────────────────────────────────────────────────────────────────┐
│                    FLUJO AUTOMÁTICO DIARIO                       │
└─────────────────────────────────────────────────────────────────┘

1. Vercel Cron Job (diario)
   ↓
2. GET /api/cron/generate-vouchers
   ├─ Crea vouchers para contratos del día
   ├─ Verifica si propiedad tiene servicios activos
   └─ Si tiene servicios →
      ↓
3. POST {AGENT_API_URL}/consultar/propiedad
   Body: {
     "propiedad_id": 35,
     "callback_url": "{NEXT_PUBLIC_APP_URL}/api/vouchers/{voucherId}/servicios-basicos"
   }
   ↓
4. Agente encola trabajo
   Response: { "job_id": "uuid", "status": "pending" }
   ↓
5. Worker procesa consultas (15-60s)
   - Abre navegador con browser-use
   - Consulta cada servicio (agua, luz, gas)
   - Guarda en consultas_deuda con consulta_id
   ↓
6. POST {callback_url}
   Body: {
     "resultados": [
       {
         "servicio_id": 5,
         "propiedad_id": 35,
         "empresa": "Metrogas",
         "tipo_servicio": "Gas",
         "deuda": 25670.0,
         "exito": true,
         "error": null,
         "consulta_id": "uuid"
       }
     ]
   }
   ↓
7. Next.js procesa callback
   - Filtra servicios exitosos con deuda > 0
   - Actualiza voucher.servicios_basicos (JSONB)
   - Marca servicios_basicos_consultados = true
   - Registra errores en tabla logs
   ↓
8. Arrendatario accede al portal de pago
   - Ve checkboxes de servicios disponibles
   - Selecciona servicios a pagar
   - Total se calcula automáticamente
```

---

## 🔧 Configuración

### 1. Variables de Entorno del Agente

```bash
# .env del agente (real-state-servicios/.env)
SUPABASE_URL=https://bkqknkqmfqqehrbppndw.supabase.co
SUPABASE_KEY=eyJhbGci...  # Service role key

BROWSER_USE_CLOUD=true
BROWSER_USE_API_KEY=bu_BX2lZKJyRhGfBuAex4FjnxrvemWIA79biP1MnIFAh4M

API_HOST=0.0.0.0
API_PORT=8000

MAX_FAILURES=3
STEP_TIMEOUT=30
MAX_ACTIONS_PER_STEP=5
```

### 2. Variables de Entorno de Next.js

```bash
# .env de Next.js (real-state/.env)
SUPABASE_URL=https://bkqknkqmfqqehrbppndw.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJhbGci...

# URL del agente (ajustar según despliegue)
AGENT_API_URL=https://tomy-real-state-servicios.0cguqx.easypanel.host

# URL de la app Next.js (para callbacks)
NEXT_PUBLIC_APP_URL=http://localhost:3000  # Dev
# NEXT_PUBLIC_APP_URL=https://tu-app.vercel.app  # Producción

CRON_SECRET=your-secret-here
```

---

## 📡 Formato del Payload de Callback

### Lo que envía el Agente

```typescript
POST {NEXT_PUBLIC_APP_URL}/api/vouchers/{voucherId}/servicios-basicos

Headers:
  Content-Type: application/json

Body:
{
  "resultados": [
    {
      "servicio_id": 5,           // bigint - ID del servicio en Supabase
      "propiedad_id": 35,          // bigint - ID de la propiedad
      "empresa": "Metrogas",       // string - Nombre de la empresa
      "tipo_servicio": "Gas",      // string - Tipo de servicio
      "deuda": 25670.0,            // number - Monto de la deuda en pesos
      "exito": true,               // boolean - true si consultó correctamente
      "error": null,               // string | null - Mensaje de error si falló
      "consulta_id": "uuid-123"    // string | null - UUID de consultas_deuda
    },
    {
      "servicio_id": 6,
      "propiedad_id": 35,
      "empresa": "Aguas Andinas",
      "tipo_servicio": "Agua",
      "deuda": 0,                  // Sin deuda
      "exito": true,
      "error": null,
      "consulta_id": "uuid-456"
    },
    {
      "servicio_id": 8,
      "propiedad_id": 35,
      "empresa": "CGE",
      "tipo_servicio": "Luz",
      "deuda": 0,
      "exito": false,
      "error": "Timeout: Portal no respondió en 30s",
      "consulta_id": "uuid-789"
    }
  ]
}
```

### Casos Especiales

**Array vacío (sin servicios):**
```json
{
  "resultados": []
}
```

**Todos los servicios fallaron:**
```json
{
  "resultados": [
    {
      "servicio_id": 5,
      "exito": false,
      "error": "Credenciales inválidas",
      "deuda": 0,
      ...
    }
  ]
}
```

---

## 🧪 Testing en Desarrollo Local

### Opción A: Usando ngrok (Recomendado)

**Paso 1: Instalar ngrok**
```bash
brew install ngrok
# o descargar de https://ngrok.com/
```

**Paso 2: Iniciar Next.js**
```bash
cd /Users/mac-tomy/Documents/prog/real-state
pnpm dev  # Corre en localhost:3000
```

**Paso 3: Exponer con ngrok**
```bash
# En otra terminal
ngrok http 3000
```

Obtendrás algo como:
```
Forwarding  https://abc123.ngrok.io -> http://localhost:3000
```

**Paso 4: Configurar callback URL**

En el código de Next.js que llama al agente:
```typescript
// app/api/cron/generate-vouchers/route.ts
const callbackUrl = process.env.NODE_ENV === 'production'
  ? `${process.env.NEXT_PUBLIC_APP_URL}/api/vouchers/${voucherId}/servicios-basicos`
  : `https://abc123.ngrok.io/api/vouchers/${voucherId}/servicios-basicos`;  // ← Usar URL de ngrok
```

**Paso 5: Iniciar el agente**
```bash
cd /Users/mac-tomy/Documents/prog/real-state-servicios
python api.py
```

**Paso 6: Hacer request de prueba**
```bash
curl -X POST http://localhost:8000/consultar/propiedad \
  -H "Content-Type: application/json" \
  -d '{
    "propiedad_id": 35,
    "callback_url": "https://abc123.ngrok.io/api/vouchers/test-voucher-123/servicios-basicos"
  }'
```

---

### Opción B: Ambos en Localhost (Solo para Testing)

Si tanto Next.js como el agente corren en la misma máquina:

```typescript
const callbackUrl = `http://localhost:3000/api/vouchers/${voucherId}/servicios-basicos`;
```

**Limitación:** Esto solo funciona localmente. En producción, usa URLs públicas.

---

## 🔍 Verificación del Callback

### 1. Verificar que el Endpoint de Next.js Responde

```bash
# Test del endpoint de callback
curl -X POST http://localhost:3000/api/vouchers/test-voucher-123/servicios-basicos \
  -H "Content-Type: application/json" \
  -d '{
    "resultados": [
      {
        "servicio_id": 5,
        "propiedad_id": 35,
        "empresa": "Metrogas",
        "tipo_servicio": "Gas",
        "deuda": 25670.0,
        "exito": true,
        "error": null,
        "consulta_id": "test-uuid-123"
      }
    ]
  }'
```

**Respuesta esperada (404 si voucher no existe):**
```json
{
  "error": "Voucher not found"
}
```

### 2. Crear un Voucher de Prueba

Primero crea un voucher en Supabase o via API de Next.js:

```sql
-- En Supabase SQL Editor
INSERT INTO vouchers (voucher_id, folio, propiedad_id, contrato_id, arrendatario_id, organizacion_id, estado, monto_arriendo, moneda, fecha_generacion, fecha_vencimiento)
VALUES (
  'test-voucher-123',
  'TEST-001',
  35,  -- propiedad_id que tiene servicios
  'contrato-uuid',
  'arrendatario-uuid',
  'org-uuid',
  'GENERADO',
  500000,
  'CLP',
  NOW(),
  CURRENT_DATE + INTERVAL '30 days'
);
```

### 3. Hacer Request Completo

```bash
# Encolar consulta con callback
curl -X POST http://localhost:8000/consultar/propiedad \
  -H "Content-Type: application/json" \
  -d '{
    "propiedad_id": 35,
    "callback_url": "https://abc123.ngrok.io/api/vouchers/test-voucher-123/servicios-basicos"
  }'
```

**Respuesta inmediata:**
```json
{
  "job_id": "d4f5a6b7-c8d9-4e0f-a1b2-c3d4e5f6a7b8",
  "status": "pending",
  "propiedad_id": 35,
  "mensaje": "Consulta encolada correctamente. Se notificará al callback cuando termine."
}
```

### 4. Monitorear Logs

**Terminal del Agente:**
```
INFO: Job d4f5a6b7... encolado - Tipo: propiedad, Posición en cola: 1, Callback: True
INFO: Worker 0 procesando job d4f5a6b7...
INFO: Consultando servicio 5 - Metrogas
INFO: Servicio 5: Deuda = $25670.0, Consulta ID: a1b2c3d4...
INFO: Job d4f5a6b7... completado exitosamente por worker 0
INFO: Enviando callback con 3 resultados para job d4f5a6b7...
INFO: Callback enviado exitosamente para job d4f5a6b7... a https://abc123.ngrok.io/...
```

**Terminal de ngrok:**
```
POST /api/vouchers/test-voucher-123/servicios-basicos  200 OK
```

**Terminal de Next.js:**
```
[Callback recibido] Voucher: test-voucher-123, Resultados: 3
[Procesando] Servicios con deuda > 0: 2
[Actualizado] Voucher test-voucher-123 con servicios básicos
```

### 5. Verificar en Supabase

```sql
-- Ver el voucher actualizado
SELECT voucher_id, servicios_basicos, servicios_basicos_consultados, fecha_consulta_servicios
FROM vouchers
WHERE voucher_id = 'test-voucher-123';
```

**Resultado esperado:**
```
voucher_id          | servicios_basicos                | servicios_basicos_consultados | fecha_consulta_servicios
--------------------|----------------------------------|-------------------------------|-------------------------
test-voucher-123    | [{"servicio_id": 5, "deuda": ... }] | true                          | 2025-01-24 10:30:00+00
```

---

## 🐛 Troubleshooting

### Problema 1: Callback No Llega a Next.js

**Síntomas:**
- El job completa (`GET /job/{job_id}` muestra `status: completed`)
- Pero el voucher no se actualiza en Supabase
- Logs del agente muestran: `ERROR: Callback falló definitivamente`

**Posibles Causas:**

1. **URL de callback incorrecta**
   ```bash
   # Verificar que la URL es accesible
   curl https://abc123.ngrok.io/api/vouchers/test-123/servicios-basicos
   ```

2. **Next.js no está corriendo**
   ```bash
   # Verificar que Next.js responde
   curl http://localhost:3000/api/health
   ```

3. **ngrok expiró (si usas plan free)**
   - ngrok free cambia la URL cada 2 horas
   - Reiniciar ngrok y actualizar la URL en el request

4. **Firewall bloqueando el callback**
   - Verificar que el agente puede hacer requests HTTP salientes

**Solución:**
```bash
# Ver detalles del error en el job
curl http://localhost:8000/job/{job_id} | jq '.callback_error'

# Si dice "Connection refused":
# - Verificar que ngrok está corriendo
# - Verificar que Next.js está corriendo

# Si dice "404 Not Found":
# - Verificar que el endpoint existe en Next.js
# - Verificar la ruta exacta del callback_url
```

---

### Problema 2: Voucher No Se Actualiza Aunque Callback Llegó

**Síntomas:**
- Logs de Next.js muestran "Callback recibido"
- Pero `vouchers.servicios_basicos` sigue vacío
- O `servicios_basicos_consultados` sigue en `false`

**Posibles Causas:**

1. **Voucher no existe en la BD**
   ```sql
   SELECT * FROM vouchers WHERE voucher_id = 'test-123';
   -- Si retorna 0 rows, el voucher no existe
   ```

2. **Todos los servicios fallaron o tienen deuda = 0**
   - Next.js solo guarda servicios con `exito: true` y `deuda > 0`
   - Verificar payload del callback en logs

3. **Error al actualizar Supabase**
   - Revisar logs de Next.js para errores de BD
   - Verificar permisos de `SUPABASE_SERVICE_ROLE_KEY`

**Solución:**
```typescript
// En el endpoint de callback, agregar más logs:
console.log('[Callback] Payload recibido:', JSON.stringify(body, null, 2));
console.log('[Callback] Servicios a guardar:', serviciosAGuardar.length);
console.log('[Callback] Voucher antes:', voucher);
console.log('[Callback] Voucher después:', updatedVoucher);
```

---

### Problema 3: Servicios con Error No Se Registran

**Síntomas:**
- Un servicio falla (timeout, portal caído)
- No aparece en logs de Next.js
- Arrendatario no sabe que el servicio no se pudo consultar

**Causa:**
El endpoint de callback de Next.js solo procesa servicios exitosos y registra errores en tabla `logs`.

**Solución:**
```typescript
// Verificar tabla logs en Supabase
SELECT * FROM logs
WHERE fuente = 'servicios-basicos-consulta'
ORDER BY fecha DESC
LIMIT 10;
```

Si no aparecen errores:
- Verificar que el agente está enviando `exito: false` para servicios fallidos
- Verificar que Next.js está guardando en tabla `logs`

---

### Problema 4: Timeout del Agente

**Síntomas:**
- El job queda en `processing` indefinidamente
- No completa ni falla
- Worker se queda "stuck"

**Posibles Causas:**
- Portal de servicio está muy lento
- Browser-use se quedó esperando elemento que nunca apareció
- Timeout configurado es muy largo

**Solución:**
```bash
# Verificar estado del job
curl http://localhost:8000/job/{job_id}

# Si está stuck, ver estadísticas de la cola
curl http://localhost:8000/queue/stats

# Reiniciar el agente si es necesario
# (los jobs en processing se perderán)
```

**Prevención:**
- Configurar `STEP_TIMEOUT` más bajo (15s en lugar de 30s)
- Configurar `MAX_FAILURES` para que falle rápido (2 en lugar de 3)

---

### Problema 5: Array Vacío de Resultados

**Síntomas:**
- Callback llega con `{ "resultados": [] }`
- Voucher no se actualiza

**Causas Comunes:**
1. Propiedad no tiene servicios activos en Supabase
2. Los servicios existen pero están con `activo = false`
3. Los IDs de servicios no coinciden con la propiedad

**Verificación:**
```sql
-- Ver servicios activos de la propiedad
SELECT servicio_id, tipo_servicio, compania, activo
FROM servicios
WHERE propiedad_id = 35;

-- Si retorna 0 rows, no hay servicios configurados
```

**Solución:**
```sql
-- Agregar servicios si no existen
INSERT INTO servicios (propiedad_id, tipo_servicio, compania, credenciales, activo)
VALUES
  (35, 'Gas', 'Metrogas', '{"identificador": "900728824"}'::jsonb, true),
  (35, 'Agua', 'Aguas Andinas', '{"identificador": "12345678"}'::jsonb, true);
```

---

## 📝 Checklist de Integración

### Pre-requisitos
- [ ] Agente desplegado y accesible via HTTP
- [ ] Next.js con endpoint `/api/vouchers/[voucherId]/servicios-basicos`
- [ ] Variables de entorno configuradas en ambos
- [ ] Supabase con tablas: `vouchers`, `servicios`, `consultas_deuda`, `logs`
- [ ] Browser-use API key válida

### Testing Local
- [ ] ngrok instalado y corriendo
- [ ] Agente responde a `GET /health`
- [ ] Next.js responde a endpoint de callback (aunque retorne 404)
- [ ] Voucher de prueba creado en Supabase
- [ ] Servicios activos configurados para la propiedad de prueba

### Test End-to-End
- [ ] Request a `/consultar/propiedad` retorna job_id
- [ ] Job procesa correctamente (ver con `GET /job/{job_id}`)
- [ ] Callback llega a Next.js (ver logs de ngrok y Next.js)
- [ ] Voucher se actualiza en Supabase
- [ ] `servicios_basicos` contiene array con servicios
- [ ] `servicios_basicos_consultados` = true
- [ ] `fecha_consulta_servicios` tiene timestamp
- [ ] Servicios con error se registran en tabla `logs`

### Producción
- [ ] Agente desplegado en Easypanel
- [ ] Next.js desplegado en Vercel
- [ ] Variables de entorno de producción configuradas
- [ ] URL de callback apunta a dominio de producción
- [ ] Vercel Cron Job configurado y activo
- [ ] Test manual con propiedad real
- [ ] Monitoreo configurado (logs, alertas)

---

## 🚀 Despliegue en Producción

### 1. Agente (Easypanel)

Ya está desplegado en:
```
https://tomy-real-state-servicios.0cguqx.easypanel.host
```

**Verificar:**
```bash
curl https://tomy-real-state-servicios.0cguqx.easypanel.host/health
```

### 2. Next.js (Vercel)

**Variables de entorno en Vercel:**
```bash
AGENT_API_URL=https://tomy-real-state-servicios.0cguqx.easypanel.host
NEXT_PUBLIC_APP_URL=https://tu-app.vercel.app
SUPABASE_URL=https://bkqknkqmfqqehrbppndw.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJhbGci...
CRON_SECRET=your-secret-here
```

### 3. Cron Job (Vercel)

**vercel.json:**
```json
{
  "crons": [
    {
      "path": "/api/cron/generate-vouchers",
      "schedule": "0 0 * * *"
    }
  ]
}
```

Ejecuta diariamente a las 00:00 UTC.

---

## 📊 Monitoreo

### Métricas Clave

1. **Jobs procesados por día**
   ```bash
   curl https://agente.com/queue/stats
   ```

2. **Callbacks exitosos vs fallidos**
   ```sql
   -- En consultas_deuda
   SELECT
     DATE(fecha_consulta) as fecha,
     COUNT(*) as total,
     SUM(CASE WHEN error IS NULL THEN 1 ELSE 0 END) as exitosos,
     SUM(CASE WHEN error IS NOT NULL THEN 1 ELSE 0 END) as fallidos
   FROM consultas_deuda
   GROUP BY DATE(fecha_consulta)
   ORDER BY fecha DESC;
   ```

3. **Vouchers con servicios consultados**
   ```sql
   SELECT
     COUNT(*) as total_vouchers,
     SUM(CASE WHEN servicios_basicos_consultados THEN 1 ELSE 0 END) as con_servicios
   FROM vouchers
   WHERE fecha_generacion >= CURRENT_DATE - INTERVAL '7 days';
   ```

---

## 🎉 Siguiente Paso: Test End-to-End

Una vez que:
1. ✅ El agente esté corriendo
2. ✅ Next.js esté corriendo
3. ✅ ngrok esté exponiendo Next.js

Ejecuta:
```bash
python test_callbacks.py
```

Este script hará un test completo del flujo.

---

¿Listo para hacer el test? 🚀
