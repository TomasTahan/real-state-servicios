# Resumen de Mejoras - Procesamiento Paralelo

## ¿Qué se mejoró?

### Antes (v1.0)
```python
# Procesamiento SECUENCIAL
for servicio in servicios:
    resultado = await procesar_servicio(servicio)
    await asyncio.sleep(2)  # Espera 2 segundos entre cada uno
```

**Problema**: Si tienes 5 servicios y cada uno tarda 30 segundos:
- Tiempo total: **5 × 30s = 150 segundos (2.5 minutos)**

### Ahora (v2.0)
```python
# Procesamiento PARALELO
tareas = [procesar_servicio(servicio) for servicio in servicios]
resultados = await asyncio.gather(*tareas)  # Todos al mismo tiempo
```

**Mejora**: Los 5 servicios se procesan simultáneamente:
- Tiempo total: **~30-40 segundos**
- **Velocidad**: 5x más rápido ⚡

---

## Cómo usar la API desplegada en VPS

### 1. Desplegar en VPS

Sigue la guía completa en `DEPLOYMENT.md`:

```bash
# En el VPS
cd /opt
git clone <tu-repo> real-state-servicios
cd real-state-servicios

# Configurar .env
cp .env.example .env
nano .env  # Completar con tus credenciales

# Instalar y arrancar
uv sync
sudo systemctl start deudas-api
```

### 2. Usar la API

#### Consultar múltiples servicios EN PARALELO

```bash
curl -X POST http://tu-vps-ip:8000/consultar/servicios \
  -H "Content-Type: application/json" \
  -d '{
    "servicio_ids": [1, 3, 5, 7, 9]
  }'
```

**Respuesta**:
```json
{
  "total_servicios": 5,
  "resultados": [
    {
      "servicio_id": 1,
      "propiedad_id": 35,
      "empresa": "Aguas Andinas",
      "deuda": 45000.0,
      "exito": true,
      "error": null
    },
    {
      "servicio_id": 3,
      "propiedad_id": 35,
      "empresa": "Enel",
      "deuda": 12000.0,
      "exito": true,
      "error": null
    }
    // ... más resultados
  ]
}
```

### 3. ¿Dónde se guardan los montos?

**Automáticamente en Supabase** en la tabla `consultas_deuda`:

```sql
SELECT * FROM consultas_deuda
WHERE propiedad_id = 35
ORDER BY fecha_consulta DESC;
```

Resultado:
```
consulta_id | servicio_id | monto_deuda | fecha_consulta
------------|-------------|-------------|----------------
uuid-123    | 1           | 45000.0     | 2025-11-23 10:30
uuid-456    | 3           | 12000.0     | 2025-11-23 10:30
```

---

## Archivos importantes

### 📄 Documentación
- `DEPLOYMENT.md` - Guía completa de despliegue en VPS
- `EJEMPLOS_USO_API.md` - Ejemplos de uso con Bash, JavaScript, Python
- `CHANGELOG.md` - Historial de cambios

### 🔧 Código modificado
- `batch_processor.py` - Ahora procesa servicios en paralelo

---

## Comparación de rendimiento

| Servicios | Antes (secuencial) | Ahora (paralelo) | Mejora |
|-----------|-------------------|------------------|--------|
| 1         | ~30s              | ~30s             | 1x     |
| 3         | ~90s              | ~30-35s          | 3x     |
| 5         | ~150s             | ~30-40s          | 5x     |
| 10        | ~300s (5 min)     | ~30-50s          | 10x    |

---

## Ejemplo de flujo completo

### Frontend (JavaScript/React)

```javascript
// 1. Obtener IDs de servicios de tu base de datos
const servicioIds = [1, 3, 5, 7];

// 2. Consultar deudas en paralelo
const response = await fetch('http://tu-vps.com/consultar/servicios', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ servicio_ids: servicioIds })
});

const data = await response.json();

// 3. Mostrar resultados
data.resultados.forEach(r => {
  console.log(`${r.empresa}: $${r.deuda}`);
});

// Output:
// Aguas Andinas: $45000
// Enel: $12000
// Metrogas: $0
// Essbio: $23000
```

### Backend (Node.js/Express)

```javascript
app.post('/api/consultar-deudas', async (req, res) => {
  const { servicioIds } = req.body;

  try {
    const response = await fetch('http://tu-vps.com/consultar/servicios', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ servicio_ids: servicioIds })
    });

    const deudas = await response.json();

    // Guardar en tu base de datos si quieres
    // O simplemente retornar al frontend
    res.json(deudas);

  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});
```

---

## Preguntas frecuentes

### ¿Cuántos servicios puedo consultar a la vez?

**Recomendado**: Hasta 10 servicios por request.

Si tienes más, divide en batches:
```javascript
const servicioIds = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12];
const batchSize = 10;

for (let i = 0; i < servicioIds.length; i += batchSize) {
  const batch = servicioIds.slice(i, i + batchSize);
  await consultarServicios(batch);
}
```

### ¿Se guarda automáticamente en la base de datos?

**Sí**. Cada consulta exitosa se guarda en Supabase (`consultas_deuda`) con:
- Monto de la deuda
- Fecha/hora de consulta
- ID del servicio
- ID de la propiedad
- Metadata (empresa, tipo de servicio)

### ¿Puedo ver el historial de consultas?

**Sí**. Usa el endpoint:
```bash
curl http://tu-vps.com/historial/propiedad/35?limit=20
```

### ¿Qué pasa si un servicio falla?

El sistema continúa procesando los demás. El resultado incluye:
```json
{
  "servicio_id": 9,
  "exito": false,
  "error": "Timeout al consultar portal"
}
```

---

## Próximos pasos sugeridos

1. **Agregar autenticación JWT** para proteger la API
2. **Implementar rate limiting** para evitar abuse
3. **Crear un dashboard web** para visualizar deudas
4. **Configurar notificaciones** (email/WhatsApp) cuando hay deudas
5. **Agregar caché Redis** para evitar consultas duplicadas recientes

---

## Soporte

Para más detalles, revisa:
- `DEPLOYMENT.md` - Despliegue completo
- `EJEMPLOS_USO_API.md` - Ejemplos prácticos
- `README.md` - Documentación general
