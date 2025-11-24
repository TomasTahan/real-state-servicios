# Guía de Uso del Sistema de Callbacks

## Descripción General

El agente de servicios básicos ahora soporta notificaciones automáticas mediante callbacks HTTP. Esto permite que tu aplicación Next.js reciba los resultados automáticamente sin necesidad de hacer polling.

## Características Implementadas

### ✅ 1. Sistema de Callbacks con Reintentos
- El agente hace un POST automático al `callback_url` cuando termina de procesar
- Reintentos automáticos (3 intentos) con backoff exponencial (1s, 2s, 4s)
- Callbacks se envían tanto para éxito como para errores
- Los fallos de callback no afectan el procesamiento del job

### ✅ 2. Consulta_id en Resultados
- Cada consulta guarda un registro en la tabla `consultas_deuda` con un `consulta_id` único
- Este ID se incluye en todos los resultados para trazabilidad
- Permite auditoría completa: conectar vouchers con consultas específicas

### ✅ 3. Endpoint de Servicios Específicos
- Nuevo endpoint `/consultar/servicios` para consultar servicios por IDs
- Útil para re-consultar servicios que fallaron
- Soporta callbacks igual que `/consultar/propiedad`

---

## Endpoints Disponibles

### 1. POST /consultar/propiedad

Consulta todos los servicios activos de una propiedad.

**Request:**
```json
{
  "propiedad_id": 35,
  "callback_url": "https://mi-app.vercel.app/api/vouchers/uuid-123/servicios-basicos",
  "voucher_id": "uuid-123"
}
```

**Respuesta Inmediata:**
```json
{
  "job_id": "d4f5a6b7-c8d9-4e0f-a1b2-c3d4e5f6a7b8",
  "status": "pending",
  "propiedad_id": 35,
  "mensaje": "Consulta encolada correctamente. Se notificará al callback cuando termine."
}
```

**Callback Enviado (después de 5-10 min):**
```json
POST https://mi-app.vercel.app/api/vouchers/uuid-123/servicios-basicos
{
  "job_id": "d4f5a6b7-c8d9-4e0f-a1b2-c3d4e5f6a7b8",
  "status": "completed",
  "voucher_id": "uuid-123",
  "propiedad_id": 35,
  "resultados": [
    {
      "servicio_id": 5,
      "propiedad_id": 35,
      "empresa": "Metrogas",
      "tipo_servicio": "Gas",
      "deuda": 25670.0,
      "exito": true,
      "error": null,
      "consulta_id": "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d"
    },
    {
      "servicio_id": 6,
      "propiedad_id": 35,
      "empresa": "Aguas Andinas",
      "tipo_servicio": "Agua",
      "deuda": 12400.0,
      "exito": true,
      "error": null,
      "consulta_id": "b2c3d4e5-f6a7-8b9c-0d1e-2f3a4b5c6d7e"
    }
  ]
}
```

---

### 2. POST /consultar/servicios

Consulta servicios específicos por sus IDs.

**Request:**
```json
{
  "servicio_ids": [5, 6, 8],
  "callback_url": "https://mi-app.vercel.app/api/vouchers/uuid-456/servicios-basicos",
  "voucher_id": "uuid-456"
}
```

**Respuesta Inmediata:**
```json
{
  "job_id": "e5f6a7b8-c9d0-4e1f-a2b3-c4d5e6f7a8b9",
  "status": "pending",
  "total_servicios": 3,
  "mensaje": "Consulta encolada correctamente. Se notificará al callback cuando termine."
}
```

**Callback:** Mismo formato que `/consultar/propiedad`

---

### 3. GET /job/{job_id}

Consulta el estado de un job (útil si no usas callback).

**Request:**
```
GET /job/d4f5a6b7-c8d9-4e0f-a1b2-c3d4e5f6a7b8
```

**Respuesta:**
```json
{
  "job_id": "d4f5a6b7-c8d9-4e0f-a1b2-c3d4e5f6a7b8",
  "tipo": "propiedad",
  "params": {"propiedad_id": 35},
  "status": "completed",
  "created_at": "2025-01-24T10:30:00",
  "started_at": "2025-01-24T10:30:05",
  "completed_at": "2025-01-24T10:35:30",
  "resultado": [...],
  "error": null,
  "callback_url": "https://...",
  "voucher_id": "uuid-123",
  "callback_sent": true,
  "callback_error": null
}
```

---

## Estructura de Resultados

Cada servicio consultado retorna:

```typescript
{
  servicio_id: number,        // ID del servicio en Supabase
  propiedad_id: number,       // ID de la propiedad
  empresa: string,            // Ej: "Metrogas", "Aguas Andinas"
  tipo_servicio: string,      // Ej: "Gas", "Agua", "Luz"
  deuda: number,              // Monto de la deuda en pesos
  exito: boolean,             // true si la consulta fue exitosa
  error: string | null,       // Mensaje de error si exito=false
  consulta_id: string | null  // UUID del registro en consultas_deuda
}
```

### Ejemplo de Servicio Exitoso:
```json
{
  "servicio_id": 5,
  "propiedad_id": 35,
  "empresa": "Metrogas",
  "tipo_servicio": "Gas",
  "deuda": 25670.0,
  "exito": true,
  "error": null,
  "consulta_id": "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d"
}
```

### Ejemplo de Servicio con Error:
```json
{
  "servicio_id": 8,
  "propiedad_id": 35,
  "empresa": "CGE",
  "tipo_servicio": "Luz",
  "deuda": 0,
  "exito": false,
  "error": "Timeout: Portal no respondió en 30s",
  "consulta_id": "c3d4e5f6-a7b8-9c0d-1e2f-3a4b5c6d7e8f"
}
```

---

## Integración con Next.js

### Crear el API Route para recibir callbacks:

**app/api/vouchers/[voucherId]/servicios-basicos/route.ts:**

```typescript
import { NextRequest, NextResponse } from 'next/server';

export async function POST(
  request: NextRequest,
  { params }: { params: { voucherId: string } }
) {
  try {
    const body = await request.json();
    const { job_id, status, resultados, voucher_id } = body;

    console.log(`Callback recibido para voucher ${params.voucherId}`);
    console.log(`Job ID: ${job_id}, Status: ${status}`);
    console.log(`Total servicios: ${resultados.length}`);

    // Validar que el voucher_id coincida
    if (voucher_id !== params.voucherId) {
      return NextResponse.json(
        { error: 'voucher_id no coincide' },
        { status: 400 }
      );
    }

    // Procesar resultados
    for (const resultado of resultados) {
      if (resultado.exito) {
        // Guardar deuda en la base de datos
        await guardarDeudaEnVoucher(
          params.voucherId,
          resultado.servicio_id,
          resultado.deuda,
          resultado.consulta_id
        );
      } else {
        // Registrar error
        console.error(
          `Error en servicio ${resultado.servicio_id}: ${resultado.error}`
        );
      }
    }

    // Actualizar estado del voucher
    if (status === 'completed') {
      await actualizarEstadoVoucher(params.voucherId, 'servicios_consultados');
    }

    return NextResponse.json({
      status: 'ok',
      mensaje: 'Resultados procesados'
    });

  } catch (error) {
    console.error('Error procesando callback:', error);
    return NextResponse.json(
      { error: 'Error interno' },
      { status: 500 }
    );
  }
}
```

### Llamar al agente desde el cron job:

```typescript
// app/api/cron/consultar-servicios/route.ts
import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  const vouchers = await obtenerVouchersPendientes();

  for (const voucher of vouchers) {
    // Llamar al agente con callback
    const response = await fetch('https://agente-url.com/consultar/propiedad', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        propiedad_id: voucher.propiedad_id,
        callback_url: `https://mi-app.vercel.app/api/vouchers/${voucher.id}/servicios-basicos`,
        voucher_id: voucher.id
      })
    });

    const data = await response.json();
    console.log(`Consulta encolada para voucher ${voucher.id}: ${data.job_id}`);

    // Guardar job_id para tracking (opcional)
    await actualizarVoucher(voucher.id, { job_id: data.job_id });
  }

  return NextResponse.json({
    mensaje: `${vouchers.length} consultas encoladas`
  });
}
```

---

## Casos de Uso

### 1. Consulta Automática Diaria (Cron Job)
```typescript
// Cada día a las 00:00
// 1. Tu cron job crea vouchers para las propiedades
// 2. Llama al agente con callback_url para cada propiedad
// 3. El agente procesa en segundo plano
// 4. Cuando termina, notifica a tu API
// 5. Tu API actualiza el voucher con las deudas
```

### 2. Re-consultar Servicios que Fallaron
```typescript
// Usuario hace clic en "Reintentar" para servicios con error
const serviciosConError = [5, 8, 12];

await fetch('https://agente-url.com/consultar/servicios', {
  method: 'POST',
  body: JSON.stringify({
    servicio_ids: serviciosConError,
    callback_url: `https://mi-app.vercel.app/api/vouchers/${voucherId}/servicios-basicos`,
    voucher_id: voucherId
  })
});
```

### 3. Consulta Manual Sin Callback (Admin)
```typescript
// Admin consulta en tiempo real con polling
const response = await fetch('https://agente-url.com/consultar/propiedad', {
  method: 'POST',
  body: JSON.stringify({ propiedad_id: 35 })
});

const { job_id } = await response.json();

// Polling cada 5 segundos
const interval = setInterval(async () => {
  const status = await fetch(`https://agente-url.com/job/${job_id}`);
  const data = await status.json();

  if (data.status === 'completed') {
    clearInterval(interval);
    mostrarResultados(data.resultado);
  }
}, 5000);
```

---

## Manejo de Errores

### Errores del Callback

Si el callback falla (ej: tu API está caída), el agente:
1. Reintenta 3 veces con backoff exponencial
2. Registra el error en `job.callback_error`
3. El job sigue marcado como `completed` (no falla el procesamiento)
4. Puedes consultar `GET /job/{job_id}` para ver los resultados

```json
{
  "status": "completed",
  "callback_sent": false,
  "callback_error": "Falló después de 3 intentos: Connection refused"
}
```

### Errores en Servicios Individuales

Si un servicio falla, el agente:
1. Marca ese servicio con `exito: false`
2. Guarda el error en `consultas_deuda`
3. Continúa procesando los demás servicios
4. El job se completa normalmente
5. El callback incluye los resultados con errores

---

## Auditoría y Trazabilidad

### Consultar Historial de una Propiedad

```bash
GET /historial/propiedad/35?limit=10
```

Retorna las últimas 10 consultas con sus `consulta_id`, montos y errores.

### Conectar Voucher con Consultas

En tu base de datos, guarda el `consulta_id` junto con cada deuda:

```sql
-- Tabla: voucher_servicios_basicos
CREATE TABLE voucher_servicios_basicos (
  id UUID PRIMARY KEY,
  voucher_id UUID REFERENCES vouchers(id),
  servicio_id INT REFERENCES servicios(servicio_id),
  monto_deuda DECIMAL(10,2),
  consulta_id UUID,  -- ← Conecta con consultas_deuda
  creado_en TIMESTAMP
);
```

Luego puedes rastrear:
- Qué voucher generó cada consulta
- Cuándo se consultó exactamente
- Si hubo errores en la consulta original

---

## Testing

### Script de Prueba Completo

```bash
python test_callbacks.py
```

Este script:
1. Inicia un servidor de callbacks en localhost:9000
2. Encola varias consultas con callbacks
3. Verifica que los callbacks se reciban correctamente
4. Valida la estructura de los resultados

### Ejemplo de Salida:
```
======================================================================
  PRUEBAS DEL SISTEMA DE CALLBACKS
======================================================================

🚀 Iniciando servidor de callbacks en puerto 9000...
✅ API principal operativa

======================================================================
  TEST 1: Callback para consulta de propiedad
======================================================================

1️⃣  Encolando consulta de propiedad con callback...
✅ Job encolado: d4f5a6b7-c8d9-4e0f-a1b2-c3d4e5f6a7b8
   Mensaje: Consulta encolada correctamente. Se notificará al callback cuando termine.

2️⃣  Esperando callback (máximo 3 minutos)...
....................
✅ Callback recibido después de 40.2s

3️⃣  Verificando contenido del callback...
   ✅ job_id existe
   ✅ voucher_id correcto
   ✅ status existe
   ✅ resultados existen
   ✅ resultados es lista

4️⃣  Verificando estructura de resultados...
   ✅ servicio_id: 5
   ✅ propiedad_id: 35
   ✅ empresa: Metrogas
   ✅ tipo_servicio: Gas
   ✅ deuda: 25670.0
   ✅ exito: True
   ✅ consulta_id: a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d

✅ TEST 1 PASÓ
======================================================================
```

---

## Preguntas Frecuentes

### ¿Cuánto tiempo tarda en procesar?
- **1 servicio**: ~2-3 minutos
- **3-4 servicios**: ~6-10 minutos
- **10+ servicios**: ~20-30 minutos

Los trabajos se procesan con 3 workers en paralelo.

### ¿Qué pasa si mi callback URL está caída?
El agente reintenta 3 veces. Si falla, puedes consultar `GET /job/{job_id}` para ver los resultados.

### ¿Puedo usar callbacks sin voucher_id?
Sí, `voucher_id` es opcional. Si no lo envías, simplemente no aparece en el callback.

### ¿Los callbacks funcionan con HTTPS?
Sí, el agente usa `httpx` que soporta HTTPS completamente.

### ¿Se guardan las consultas fallidas?
Sí, todas las consultas (exitosas y fallidas) se guardan en `consultas_deuda` con su `consulta_id` y mensaje de error.

---

## Resumen de Cambios

### ✅ Implementado

1. **Sistema de Callbacks**
   - Parámetros `callback_url` y `voucher_id` en requests
   - POST automático al callback cuando termina
   - Reintentos con backoff exponencial
   - Callbacks para éxito y error

2. **Consulta ID**
   - `database.py` retorna `consulta_id` al guardar
   - `batch_processor.py` captura y retorna el ID
   - Incluido en todos los resultados (éxito y error)

3. **Endpoint de Servicios Específicos**
   - Ya existía `/consultar/servicios`
   - Actualizado para soportar callbacks
   - Filtra solo servicios activos

### 📝 Notas de Migración

- **Backward compatible**: Consultas sin `callback_url` funcionan igual que antes
- **No breaking changes**: Endpoints existentes mantienen su comportamiento
- **Nuevos campos opcionales**: `callback_url`, `voucher_id`, `consulta_id`

---

## Soporte

Para reportar problemas o sugerir mejoras, revisa los logs del agente:

```bash
# Ver logs en tiempo real
tail -f logs/agente.log

# Buscar callbacks fallidos
grep "callback_error" logs/agente.log
```
