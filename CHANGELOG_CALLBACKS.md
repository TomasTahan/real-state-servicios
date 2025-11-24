# Changelog - Sistema de Callbacks

## Fecha: 2025-01-24

### 🎯 Objetivo
Implementar un sistema de callbacks para notificación automática de resultados, permitiendo que la aplicación Next.js reciba los resultados sin necesidad de hacer polling.

---

## 📋 Cambios Implementados

### 1. Sistema de Callbacks con Reintentos ✅

**Archivos modificados:**
- `api.py`
- `job_queue.py`

**Funcionalidad:**
- Nuevos parámetros opcionales en los endpoints:
  - `callback_url`: URL donde enviar los resultados
  - `voucher_id`: ID del voucher para referencia
- Sistema de reintentos con backoff exponencial (3 intentos: 1s, 2s, 4s)
- Callbacks se envían tanto para éxito como para errores
- Si el callback falla, el job NO falla (se registra el error)

**Métodos agregados:**
- `JobQueue._send_callback()`: Envía POST al callback con reintentos
- Modificado `JobQueue.add_job()`: Ahora acepta `callback_url` y `voucher_id`
- Modificado `JobQueue._worker()`: Llama a callback al terminar

**Payload del callback:**
```json
{
  "job_id": "uuid",
  "status": "completed" | "failed",
  "voucher_id": "uuid-opcional",
  "propiedad_id": 35,
  "resultados": [...]
}
```

---

### 2. Inclusión de consulta_id en Resultados ✅

**Archivos modificados:**
- `database.py`
- `batch_processor.py`

**Funcionalidad:**
- `guardar_consulta_deuda()` ahora retorna:
  ```python
  {
    "consulta_id": "uuid-generado",
    "guardado": True
  }
  ```
- Todos los resultados incluyen `consulta_id` para trazabilidad
- Consultas fallidas también se guardan en BD con su error

**Estructura de resultados actualizada:**
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

---

### 3. Endpoint de Servicios Específicos ✅

**Archivos modificados:**
- `api.py` (endpoint ya existía, actualizado con callbacks)
- `database.py` (agregado filtro `activo=True`)

**Funcionalidad:**
- `POST /consultar/servicios` permite consultar servicios por IDs
- Soporta `callback_url` y `voucher_id`
- Útil para re-consultar servicios que fallaron
- Solo consulta servicios activos

**Request:**
```json
{
  "servicio_ids": [5, 8, 12],
  "callback_url": "https://...",
  "voucher_id": "uuid-123"
}
```

---

## 📁 Archivos Modificados

### api.py
**Líneas modificadas:** 22-31, 77-96, 114-133
**Cambios:**
- Agregados campos `callback_url` y `voucher_id` a modelos Pydantic
- Endpoints pasan estos parámetros al job queue
- Mensajes de respuesta actualizados según presencia de callback

### job_queue.py
**Líneas modificadas:** 1-11, 31-70, 72-127, 181-202
**Cambios:**
- Import de `httpx` para enviar callbacks
- `add_job()` acepta `callback_url` y `voucher_id`
- Nuevos campos en job dict: `callback_url`, `voucher_id`, `callback_sent`, `callback_error`
- Método `_send_callback()` con lógica de reintentos
- Workers llaman a callback al completar/fallar

### database.py
**Líneas modificadas:** 31-61, 70-73
**Cambios:**
- `guardar_consulta_deuda()` retorna dict con `consulta_id` y `guardado`
- `get_servicios_por_ids()` filtra por `activo=True`

### batch_processor.py
**Líneas modificadas:** 41-68, 58-78, 80-106
**Cambios:**
- Captura `consulta_id` al guardar en BD
- Retorna `consulta_id` en todos los resultados
- Guarda consultas fallidas en BD con error
- Agregado campo `tipo_servicio` a resultados

---

## 📝 Archivos Nuevos

### test_callbacks.py
Script de prueba completo para validar:
- Callbacks con propiedad
- Callbacks con servicios específicos
- Modo tradicional sin callback
- Servidor de callbacks mock incluido

**Uso:**
```bash
python test_callbacks.py
```

### CALLBACKS_GUIDE.md
Documentación completa con:
- Descripción de características
- Ejemplos de request/response
- Integración con Next.js
- Casos de uso
- FAQ y troubleshooting

---

## 🔄 Backward Compatibility

### ✅ Totalmente Compatible
- Todos los endpoints existentes funcionan igual
- `callback_url` y `voucher_id` son **opcionales**
- Si no se proporciona callback, el comportamiento es idéntico a antes
- Polling con `GET /job/{job_id}` sigue funcionando

### Ejemplos:

**Antes (sigue funcionando):**
```json
POST /consultar/propiedad
{
  "propiedad_id": 35
}
```

**Ahora (opcional):**
```json
POST /consultar/propiedad
{
  "propiedad_id": 35,
  "callback_url": "https://...",
  "voucher_id": "uuid-123"
}
```

---

## 🧪 Testing

### Tests Automatizados
```bash
# Test del sistema completo (incluye callbacks)
python test_callbacks.py

# Test del sistema de cola (sin callbacks)
python test_queue_system.py
```

### Test Manual con curl

**1. Consulta con callback:**
```bash
curl -X POST http://localhost:8000/consultar/propiedad \
  -H "Content-Type: application/json" \
  -d '{
    "propiedad_id": 35,
    "callback_url": "https://webhook.site/tu-url-unica",
    "voucher_id": "test-123"
  }'
```

**2. Verificar estado del job:**
```bash
curl http://localhost:8000/job/{job_id}
```

**3. Ver estadísticas:**
```bash
curl http://localhost:8000/queue/stats
```

---

## 📊 Campos Nuevos en Job Status

Al consultar `GET /job/{job_id}`, ahora incluye:

```json
{
  "job_id": "uuid",
  "status": "completed",
  "resultado": [...],

  // NUEVOS CAMPOS:
  "callback_url": "https://...",
  "voucher_id": "uuid-123",
  "callback_sent": true,
  "callback_error": null
}
```

**callback_sent:**
- `true`: Callback enviado exitosamente
- `false`: Callback falló después de 3 intentos

**callback_error:**
- `null`: No hubo error
- `string`: Mensaje de error si falló

---

## 🚀 Rendimiento

### Sin Cambios
- El procesamiento de servicios mantiene el mismo rendimiento
- Los callbacks se envían **después** de completar el procesamiento
- No agregan latencia al procesamiento principal

### Tiempos Típicos
- **Procesamiento**: 2-3 min por servicio (sin cambios)
- **Callback**: < 5 segundos (con reintentos)
- **Total para 4 servicios**: ~10 minutos + callback

---

## 🔒 Seguridad

### Consideraciones
1. **Timeout de callbacks**: 30 segundos por intento
2. **No hay autenticación**: Considera agregar API keys si necesitas seguridad
3. **HTTPS soportado**: Usa HTTPS en producción
4. **Rate limiting**: El agente reintenta máximo 3 veces

### Recomendaciones
```typescript
// En tu API de Next.js, valida el voucher_id
export async function POST(request: NextRequest) {
  const { voucher_id } = await request.json();

  // Verificar que el voucher existe
  const voucher = await db.voucher.findUnique({
    where: { id: voucher_id }
  });

  if (!voucher) {
    return NextResponse.json(
      { error: 'Voucher no encontrado' },
      { status: 404 }
    );
  }

  // Procesar resultados...
}
```

---

## 📈 Monitoreo

### Logs a Revisar

**Callback exitoso:**
```
INFO: Callback enviado exitosamente para job d4f5a6b7... a https://...
```

**Callback con reintentos:**
```
WARNING: Error enviando callback para job d4f5a6b7...: Intento 1/3 falló: Connection refused
WARNING: Error enviando callback para job d4f5a6b7...: Intento 2/3 falló: Connection refused
INFO: Callback enviado exitosamente para job d4f5a6b7... a https://...
```

**Callback fallido:**
```
ERROR: Callback falló definitivamente para job d4f5a6b7...: Connection refused
```

### Consultar Callbacks Fallidos

```bash
# En API
curl http://localhost:8000/jobs?status=completed | jq '.jobs[] | select(.callback_sent == false)'

# Ver detalles de un job específico
curl http://localhost:8000/job/{job_id} | jq '.callback_error'
```

---

## 🐛 Troubleshooting

### Problema: Callback no se recibe

**Verificar:**
1. ¿El job está completado?
   ```bash
   curl http://localhost:8000/job/{job_id} | jq '.status'
   ```

2. ¿El callback se envió?
   ```bash
   curl http://localhost:8000/job/{job_id} | jq '.callback_sent'
   ```

3. ¿Hay error en el callback?
   ```bash
   curl http://localhost:8000/job/{job_id} | jq '.callback_error'
   ```

**Soluciones:**
- Si `callback_sent: false`, revisar `callback_error`
- Verificar que tu API esté accesible desde el agente
- Usar webhook.site para debug

### Problema: Consulta_id es null

**Causa:** Error al guardar en Supabase

**Verificar:**
- Variables de entorno `SUPABASE_URL` y `SUPABASE_KEY`
- Permisos de la tabla `consultas_deuda`
- Logs del agente para errores de BD

---

## 📦 Dependencias Nuevas

### httpx
Agregado para enviar callbacks HTTP.

**Instalación:**
```bash
pip install httpx
```

**O con uv:**
```bash
uv add httpx
```

---

## 🎯 Próximos Pasos (Opcional)

### Mejoras Futuras
1. **Autenticación de callbacks**: JWT o API keys
2. **Webhooks con firma**: HMAC para validar origen
3. **Callbacks parciales**: Notificar por cada servicio (no esperar a todos)
4. **Dashboard**: UI para ver callbacks fallidos
5. **Métricas**: Prometheus/Grafana para monitorear callbacks

---

## 📞 Soporte

Para preguntas o problemas:
1. Revisar `CALLBACKS_GUIDE.md` para ejemplos
2. Ejecutar `python test_callbacks.py` para validar setup
3. Revisar logs del agente

---

## ✅ Resumen Ejecutivo

### Lo que se Implementó:
1. ✅ Sistema de callbacks con reintentos automáticos
2. ✅ Inclusión de `consulta_id` en todos los resultados
3. ✅ Endpoint de servicios específicos ya existía (actualizado)

### Backward Compatibility:
- ✅ 100% compatible con código existente
- ✅ Todos los campos nuevos son opcionales
- ✅ No breaking changes

### Testing:
- ✅ Script de prueba completo incluido
- ✅ Documentación exhaustiva
- ✅ Ejemplos de integración con Next.js

### Listo para Producción:
- ✅ Manejo robusto de errores
- ✅ Reintentos con backoff exponencial
- ✅ Logging completo
- ✅ Auditoría con consulta_id
