# Preguntas para el Agente de Next.js

## Contexto
Acabamos de implementar un sistema de callbacks en el agente de servicios básicos. Antes de hacer los tests de integración, necesitamos validar algunos aspectos de la aplicación Next.js.

---

## 🔍 Preguntas Críticas

### 1. Estructura de Vouchers y Servicios Básicos

**Pregunta:**
¿Cómo está estructurada la tabla/modelo de vouchers en tu base de datos? Específicamente necesito saber:

- ¿Existe un modelo `Voucher` o similar?
- ¿Tiene un campo para almacenar el estado del voucher? (ej: `estado`, `status`)
- ¿Cómo se almacenan los servicios básicos relacionados a un voucher?
  - ¿Tabla separada `voucher_servicios_basicos`?
  - ¿Campo JSONB en el voucher?
  - ¿Relación con tabla `servicios` de Supabase?

**Necesito esto para:**
Saber cómo guardar los resultados del callback (deudas de servicios) en tu base de datos.

**Ideal:**
```typescript
// Ejemplo de estructura esperada
interface Voucher {
  id: string;
  propiedad_id: number;
  estado: 'pendiente' | 'servicios_consultados' | 'completado';
  created_at: Date;
  // ... otros campos
}

interface VoucherServicioBasico {
  id: string;
  voucher_id: string;
  servicio_id: number;
  empresa: string;
  tipo_servicio: string;
  monto_deuda: number;
  consulta_id: string; // ← del agente
  created_at: Date;
}
```

---

### 2. Endpoint de Callback Actual

**Pregunta:**
¿Ya existe un endpoint en tu API de Next.js para recibir callbacks? Si existe:

- ¿Cuál es la ruta? (ej: `/api/vouchers/[voucherId]/servicios-basicos`)
- ¿Qué estructura de payload espera?
- ¿Qué hace actualmente con los datos?

**Si NO existe:**
Necesito saber dónde quieres que lo cree y qué convenciones de nombres usas en tu proyecto.

---

### 3. Cron Job de Consulta Diaria

**Pregunta:**
¿Cómo funciona actualmente el cron job que crea vouchers?

- ¿Usa Vercel Cron Jobs o algún servicio externo?
- ¿Ya tiene lógica para llamar al agente de servicios básicos?
- ¿Qué hace actualmente después de crear un voucher?
  - ¿Hace polling al agente?
  - ¿Solo crea el voucher y espera procesamiento manual?

**Necesito esto para:**
Saber dónde integrar las llamadas al agente con callbacks.

---

### 4. URL de la Aplicación en Producción

**Pregunta:**
¿Cuál es la URL de tu aplicación Next.js?

- **En desarrollo:** Probablemente `http://localhost:3000`
- **En staging/producción:** ¿`https://tuapp.vercel.app`?

**Necesito esto para:**
Configurar el `callback_url` correcto en las pruebas.

---

### 5. Autenticación del Callback

**Pregunta:**
¿Tu API de Next.js tiene autenticación?

- ¿Necesito incluir headers de autenticación (API key, JWT, etc.)?
- ¿O es suficiente validar que el `voucher_id` existe en tu BD?

**Ejemplo:**
```typescript
// ¿Necesitas algo así?
headers: {
  'Authorization': 'Bearer token',
  'X-API-Key': 'key'
}
```

---

### 6. Base de Datos

**Pregunta:**
¿Usas el mismo Supabase para vouchers que para servicios?

- **Si es el mismo:** Perfecto, puedo acceder a ambas tablas
- **Si es diferente:** ¿Cómo se conectan los datos?

**Conexión:**
- Vouchers: ¿Tienen un campo `propiedad_id` que conecta con `propiedades.propiedad_id`?
- Servicios: Ya sé que están en `servicios` con `propiedad_id`

---

### 7. Flujo Actual del Usuario

**Pregunta:**
¿Cómo interactúa el admin/usuario con los vouchers actualmente?

**Ejemplo de flujo:**
1. Cron job crea vouchers cada día
2. Admin entra a la app y ve lista de vouchers
3. Admin hace clic en "Consultar servicios" (¿manualmente?)
4. ¿Qué pasa después?

**O es automático:**
1. Cron job crea vouchers
2. Cron job automáticamente encola consultas al agente
3. Agente notifica via callback
4. Voucher se actualiza automáticamente

---

### 8. Manejo de Errores

**Pregunta:**
Cuando un servicio falla (timeout, portal caído, etc.), ¿qué quieres mostrar al usuario?

**Opciones:**
- A) Guardar el error y mostrar "Servicio no disponible - Reintentar"
- B) No guardar nada y solo mostrar servicios exitosos
- C) Marcar como "Error - Consultar manualmente"

**Necesito saber:**
¿Quieres que el admin pueda reintentar servicios fallidos desde la UI?

---

### 9. Re-consulta de Servicios

**Pregunta:**
¿Necesitas UI para re-consultar servicios específicos?

**Caso de uso:**
- Un voucher tiene 4 servicios
- 3 consultaron bien, 1 falló
- Admin hace clic en "Reintentar" en el servicio fallido
- Se encola solo ese servicio (usando `/consultar/servicios`)

**¿Esto es necesario o solo quieres re-consultar toda la propiedad?**

---

### 10. Testing en Desarrollo

**Pregunta:**
Para hacer pruebas locales, ¿puedo usar ngrok o un túnel similar?

**Escenario:**
- Agente corre en localhost:8000
- Next.js corre en localhost:3000
- Necesito que el agente pueda enviar callbacks a Next.js

**Opciones:**
A) Usar ngrok: `ngrok http 3000` → `https://abc123.ngrok.io/api/callback`
B) Ambos en localhost (pero el agente debe saber tu IP local)
C) Desplegar agente temporalmente en un servidor público

**¿Cuál prefieres?**

---

## 📋 Información que YA Tengo del Agente

Para que sepas qué envía el agente:

### Payload del Callback:
```json
POST {callback_url}
{
  "job_id": "uuid-del-job",
  "status": "completed" | "failed",
  "voucher_id": "uuid-del-voucher",
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
      "consulta_id": "uuid-de-la-consulta"
    }
  ]
}
```

### Endpoints Disponibles:
1. `POST /consultar/propiedad` - Consulta todos los servicios de una propiedad
2. `POST /consultar/servicios` - Consulta servicios específicos por IDs
3. `GET /job/{job_id}` - Ver estado y resultado de un job
4. `GET /historial/propiedad/{id}` - Ver historial de consultas

---

## 🎯 Objetivo del Test

Una vez que respondas estas preguntas, voy a:

1. **Crear el endpoint de callback** en tu Next.js (si no existe)
2. **Actualizar el cron job** para usar callbacks
3. **Hacer un test end-to-end:**
   - Cron job crea voucher
   - Llama al agente con callback
   - Agente procesa en background
   - Agente envía callback a Next.js
   - Next.js guarda resultados en BD
   - Verificar que todo funcionó

4. **Documentar** el flujo completo con capturas de pantalla/logs

---

## 📝 Formato de Respuesta (Sugerido)

Para facilitarme la vida, puedes responder así:

```
1. Estructura de Vouchers:
   - Modelo: [nombre del modelo]
   - Campos principales: [lista]
   - Relación con servicios: [explicación]

2. Endpoint de Callback:
   - Estado actual: Existe / No existe
   - Ruta: [ruta si existe]

3. Cron Job:
   - Tipo: Vercel Cron / Otro
   - Hace: [descripción breve]

4. URL Producción:
   - Dev: http://localhost:3000
   - Prod: https://...

... etc
```

---

## 🚨 Urgente

Si tienes un deadline o necesitas esto funcionando YA, dime:
- ¿Para cuándo lo necesitas?
- ¿Prefieres un MVP rápido o implementación completa?
- ¿Hay alguna parte más crítica que otra?

Así priorizo correctamente.

---

¿Listo para responder? 🚀
