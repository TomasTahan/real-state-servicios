# Respuestas a Preguntas del Agente Next.js

## 1. Validación del Callback

### ❌ Sin Autenticación Actualmente

**Respuesta:** El callback se envía **sin autenticación** en la implementación actual.

**Detalles técnicos:**
```python
# En job_queue.py línea 104-106
async with httpx.AsyncClient(timeout=30.0) as client:
    response = await client.post(callback_url, json=payload)
    response.raise_for_status()
```

No se incluyen headers de autenticación, tokens, ni firmas HMAC.

### ⚠️ Implicaciones de Seguridad

**Lo que significa:**
- Cualquiera que conozca tu `callback_url` podría enviar POST maliciosos
- Debes validar en tu endpoint que el `voucher_id` existe en tu BD
- No confíes ciegamente en los datos del callback

### ✅ Recomendación para tu Endpoint Next.js

```typescript
// app/api/vouchers/[voucherId]/servicios-basicos/route.ts
export async function POST(
  request: NextRequest,
  { params }: { params: { voucherId: string } }
) {
  const body = await request.json();
  const { voucher_id, job_id, resultados } = body;

  // CRÍTICO: Validar que el voucher existe y te pertenece
  const voucher = await prisma.voucher.findUnique({
    where: { id: voucher_id }
  });

  if (!voucher) {
    return NextResponse.json(
      { error: 'Voucher no encontrado' },
      { status: 404 }
    );
  }

  // CRÍTICO: Validar que el voucher_id del URL coincide con el del body
  if (voucher_id !== params.voucherId) {
    return NextResponse.json(
      { error: 'voucher_id no coincide' },
      { status: 400 }
    );
  }

  // Ahora es seguro procesar los resultados...
}
```

### 🔐 Si Necesitas Agregar Autenticación

**Opción A: API Key Simple**

Si quieres que agreguemos autenticación, puedo modificar el callback para enviar:

```python
headers = {
    'X-API-Key': settings.CALLBACK_API_KEY,
    'Content-Type': 'application/json'
}
response = await client.post(callback_url, json=payload, headers=headers)
```

Y en tu Next.js:
```typescript
const apiKey = request.headers.get('X-API-Key');
if (apiKey !== process.env.AGENTE_API_KEY) {
  return NextResponse.json({ error: 'No autorizado' }, { status: 401 });
}
```

**Opción B: HMAC Signature (Más Seguro)**

Similar a webhooks de Stripe/GitHub. Si lo necesitas, puedo implementarlo.

---

## 2. Formato del Campo consulta_id

### ✅ UUID (string)

**Respuesta:** `consulta_id` es un **UUID en formato string**.

**Detalles técnicos:**
```python
# En database.py línea 56-60
if response.data and len(response.data) > 0:
    return {
        "consulta_id": response.data[0].get("consulta_id"),  # ← UUID string
        "guardado": True
    }
```

Supabase lo retorna como string en formato: `"a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d"`

### 📝 Tipado en TypeScript

```typescript
interface ResultadoServicio {
  servicio_id: number;
  propiedad_id: number;
  empresa: string;
  tipo_servicio: string;
  deuda: number;
  exito: boolean;
  error: string | null;
  consulta_id: string | null;  // ← UUID string o null si falló el guardado
}
```

### ⚠️ Casos donde consulta_id es null

El `consulta_id` puede ser `null` en estos casos:
1. Error al guardar en Supabase (raro, pero posible)
2. Error de conexión con Supabase durante el guardado

**Ejemplo de manejo:**
```typescript
for (const resultado of resultados) {
  if (resultado.consulta_id) {
    // Guardar con referencia a la consulta original
    await prisma.voucherServicio.create({
      data: {
        voucher_id: voucherId,
        servicio_id: resultado.servicio_id,
        monto_deuda: resultado.deuda,
        consulta_id: resultado.consulta_id,  // UUID string
        exito: resultado.exito
      }
    });
  } else {
    // Log de warning - no se pudo obtener consulta_id
    console.warn(
      `Resultado sin consulta_id para servicio ${resultado.servicio_id}`
    );
  }
}
```

---

## 3. Comportamiento con Servicios Vacíos

### 📊 Comportamiento Actual

Verifiqué el código y aquí está el comportamiento exacto:

#### Caso 1: Array Vacío `servicio_ids: []`

**Request:**
```json
POST /consultar/servicios
{
  "servicio_ids": []
}
```

**Respuesta:**
```json
{
  "job_id": "uuid-generado",
  "status": "pending",
  "total_servicios": 0,
  "mensaje": "Consulta encolada correctamente"
}
```

**Comportamiento:**
- ✅ El job se encola sin error
- ✅ El worker procesa el job
- ✅ `db.get_servicios_por_ids([])` retorna array vacío
- ✅ `procesar_servicios_especificos()` procesa 0 servicios
- ✅ El job completa con `resultado: []`
- ✅ Si hay callback, se envía con `resultados: []`

**Código relevante:**
```python
# En batch_processor.py línea 161
servicios = db.get_servicios_por_ids(servicio_ids)  # Retorna []

# Línea 173-174
tareas = [procesar_con_runner(servicio) for servicio in servicios]  # []
resultados = await asyncio.gather(*tareas)  # []
```

#### Caso 2: IDs que no Existen

**Request:**
```json
POST /consultar/servicios
{
  "servicio_ids": [999, 888, 777]
}
```

**Comportamiento:**
- ✅ El job se encola
- ✅ `db.get_servicios_por_ids([999, 888, 777])` consulta Supabase
- ✅ Supabase retorna array vacío (no encuentra esos IDs)
- ✅ El job completa con `resultado: []`

**Código relevante:**
```python
# En database.py línea 72
response = self.client.table("servicios")
    .select("*")
    .in_("servicio_id", servicio_ids)  # [999, 888, 777]
    .eq("activo", True)
    .execute()
return response.data  # [] si no encuentra ninguno
```

#### Caso 3: Mezcla de IDs Válidos e Inválidos

**Request:**
```json
POST /consultar/servicios
{
  "servicio_ids": [5, 999, 8]
}
```

**Comportamiento:**
- ✅ Solo procesa los servicios que existen (5 y 8)
- ✅ Ignora silenciosamente el 999
- ✅ `resultado: [{servicio_id: 5, ...}, {servicio_id: 8, ...}]`

### ❌ NO Valida IDs Antes de Encolar

**Importante:** El endpoint NO valida que los IDs existan antes de encolar el job. La validación ocurre durante el procesamiento.

**Por qué es así:**
- La validación requiere consultar Supabase
- Queremos que el encolado sea rápido (<100ms)
- La consulta real puede tardar minutos

### ✅ Recomendaciones para tu Next.js

**1. Validar antes de llamar al agente:**
```typescript
// Antes de encolar
if (servicioIds.length === 0) {
  return NextResponse.json(
    { error: 'Debe proporcionar al menos un servicio_id' },
    { status: 400 }
  );
}

// Opcional: Verificar que existen en tu BD
const serviciosExistentes = await prisma.servicio.findMany({
  where: { id: { in: servicioIds } }
});

if (serviciosExistentes.length === 0) {
  return NextResponse.json(
    { error: 'Ninguno de los servicios existe' },
    { status: 404 }
  );
}
```

**2. Manejar resultados vacíos en el callback:**
```typescript
export async function POST(request: NextRequest) {
  const { resultados, voucher_id } = await request.json();

  if (resultados.length === 0) {
    // Caso: No se consultó ningún servicio
    // Puede ser porque no existen o porque son todos inactivos
    await logWarning(`Callback con resultados vacíos para voucher ${voucher_id}`);

    return NextResponse.json({
      status: 'ok',
      mensaje: 'Sin resultados para procesar'
    });
  }

  // Procesar resultados...
}
```

**3. Detectar servicios que no se procesaron:**
```typescript
// Enviaste [5, 999, 8] pero solo recibiste resultados para [5, 8]
const serviciosEnviados = [5, 999, 8];
const serviciosRecibidos = resultados.map(r => r.servicio_id);
const serviciosNoProcessados = serviciosEnviados.filter(
  id => !serviciosRecibidos.includes(id)
);

if (serviciosNoProcessados.length > 0) {
  console.warn(
    `Servicios no procesados (no existen o inactivos): ${serviciosNoProcessados}`
  );
}
```

---

## 📊 Tabla Resumen

| Escenario | Request | Job Se Encola | Resultado | Callback |
|-----------|---------|---------------|-----------|----------|
| Array vacío | `servicio_ids: []` | ✅ Sí | `resultado: []` | ✅ Se envía |
| IDs inexistentes | `servicio_ids: [999]` | ✅ Sí | `resultado: []` | ✅ Se envía |
| IDs válidos | `servicio_ids: [5, 8]` | ✅ Sí | `resultado: [{...}, {...}]` | ✅ Se envía |
| Mezcla | `servicio_ids: [5, 999]` | ✅ Sí | `resultado: [{servicio_id: 5}]` | ✅ Se envía |
| IDs inactivos | `servicio_ids: [10]` (inactivo) | ✅ Sí | `resultado: []` | ✅ Se envía |

---

## 🐛 Edge Cases Adicionales

### Caso 4: Tipos de Datos Incorrectos

**Request:**
```json
POST /consultar/servicios
{
  "servicio_ids": ["5", "8"]  // ❌ Strings en lugar de números
}
```

**Respuesta:**
```json
{
  "detail": [
    {
      "type": "int_parsing",
      "loc": ["body", "servicio_ids", 0],
      "msg": "Input should be a valid integer"
    }
  ]
}
```

FastAPI/Pydantic valida los tipos antes de llegar al handler.

### Caso 5: Campo Faltante

**Request:**
```json
POST /consultar/servicios
{
  "callback_url": "https://..."
  // ❌ Falta servicio_ids
}
```

**Respuesta:**
```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "servicio_ids"],
      "msg": "Field required"
    }
  ]
}
```

---

## 🔧 Si Quieres Cambiar el Comportamiento

Si prefieres que el agente valide y rechace arrays vacíos o IDs inválidos **antes** de encolar, puedo modificar el endpoint así:

```python
@app.post("/consultar/servicios")
async def consultar_servicios(request: ConsultaServiciosRequest):
    # Validación antes de encolar
    if not request.servicio_ids:
        raise HTTPException(
            status_code=400,
            detail="servicio_ids no puede estar vacío"
        )

    # Verificar que al menos uno existe
    servicios = db.get_servicios_por_ids(request.servicio_ids)
    if not servicios:
        raise HTTPException(
            status_code=404,
            detail="Ninguno de los servicios proporcionados existe o está activo"
        )

    # Solo encolar si hay servicios válidos
    job_id = await job_queue.add_job(...)
```

**¿Quieres que implemente esta validación?**

---

## ✅ Resumen para Implementación

### En tu Next.js debes:

1. **Validar voucher_id** en el endpoint de callback (crítico)
2. **Tipar consulta_id** como `string | null`
3. **Manejar resultados vacíos** sin crashear
4. **Validar servicios antes de encolar** (opcional pero recomendado)
5. **No confiar ciegamente** en los datos del callback (sin autenticación)

### Código que puedo agregar si lo necesitas:

1. ✅ **Autenticación con API Key** - 5 minutos
2. ✅ **Validación pre-encolado** - 10 minutos
3. ✅ **HMAC Signatures** - 30 minutos (más seguro)

---

## 🚀 Próximos Pasos

Con esta información ya puedes:
1. Implementar el endpoint de callback en Next.js con las validaciones correctas
2. Manejar todos los edge cases
3. Decidir si necesitas agregar autenticación

**¿Necesitas que implemente alguna de las mejoras sugeridas o estás listo para hacer el test end-to-end?**
