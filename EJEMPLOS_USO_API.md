# Ejemplos de Uso de la API

## URL Base

```
http://tu-vps-ip:8000
```

O con dominio:
```
https://tu-dominio.com
```

---

## 1. Consultar servicios específicos (PARALELO)

### Caso de uso
Cuando tienes una lista de servicios (IDs) y quieres consultar sus deudas en paralelo para obtener resultados más rápido.

### Request

```bash
curl -X POST http://tu-vps-ip:8000/consultar/servicios \
  -H "Content-Type: application/json" \
  -d '{
    "servicio_ids": [1, 3, 5, 7, 9]
  }'
```

### Desde JavaScript/TypeScript

```javascript
const response = await fetch('http://tu-vps-ip:8000/consultar/servicios', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    servicio_ids: [1, 3, 5, 7, 9]
  })
});

const data = await response.json();
console.log(data);
```

### Desde Python

```python
import requests

url = "http://tu-vps-ip:8000/consultar/servicios"
payload = {
    "servicio_ids": [1, 3, 5, 7, 9]
}

response = requests.post(url, json=payload)
data = response.json()
print(data)
```

### Response

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
    },
    {
      "servicio_id": 5,
      "propiedad_id": 40,
      "empresa": "Metrogas",
      "deuda": 0.0,
      "exito": true,
      "error": null
    },
    {
      "servicio_id": 7,
      "propiedad_id": 40,
      "empresa": "Essbio",
      "deuda": 23000.0,
      "exito": true,
      "error": null
    },
    {
      "servicio_id": 9,
      "propiedad_id": 42,
      "empresa": "CGE",
      "exito": false,
      "error": "Timeout al consultar portal"
    }
  ]
}
```

**Nota**: Los montos se guardan automáticamente en Supabase en la tabla `consultas_deuda`.

---

## 2. Consultar todas las deudas de una propiedad

### Caso de uso
Cuando quieres saber todas las deudas de todos los servicios asociados a una propiedad específica.

### Request

```bash
curl -X POST http://tu-vps-ip:8000/consultar/propiedad \
  -H "Content-Type: application/json" \
  -d '{
    "propiedad_id": 35
  }'
```

### Desde JavaScript

```javascript
const response = await fetch('http://tu-vps-ip:8000/consultar/propiedad', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    propiedad_id: 35
  })
});

const data = await response.json();
console.log(`Total deuda: ${data.resultados.reduce((sum, r) => sum + r.deuda, 0)}`);
```

### Response

```json
{
  "propiedad_id": 35,
  "total_servicios": 3,
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
      "servicio_id": 2,
      "propiedad_id": 35,
      "empresa": "Enel",
      "deuda": 12000.0,
      "exito": true,
      "error": null
    },
    {
      "servicio_id": 3,
      "propiedad_id": 35,
      "empresa": "Metrogas",
      "deuda": 0.0,
      "exito": true,
      "error": null
    }
  ]
}
```

---

## 3. Ver historial de consultas de una propiedad

### Caso de uso
Ver el historial de consultas pasadas para analizar tendencias de deuda.

### Request

```bash
# Últimas 10 consultas (default)
curl http://tu-vps-ip:8000/historial/propiedad/35

# Últimas 50 consultas
curl http://tu-vps-ip:8000/historial/propiedad/35?limit=50
```

### Desde JavaScript

```javascript
const propiedadId = 35;
const limit = 20;
const response = await fetch(
  `http://tu-vps-ip:8000/historial/propiedad/${propiedadId}?limit=${limit}`
);

const data = await response.json();
console.log(data);
```

### Response

```json
{
  "propiedad_id": 35,
  "total_registros": 10,
  "historial": [
    {
      "consulta_id": "550e8400-e29b-41d4-a716-446655440000",
      "servicio_id": 1,
      "propiedad_id": 35,
      "monto_deuda": 45000.0,
      "fecha_consulta": "2025-11-23T10:30:00.000Z",
      "metadata": {
        "empresa": "Aguas Andinas",
        "tipo": "Agua"
      },
      "servicios": {
        "tipo_servicio": "Agua",
        "compania": "Aguas Andinas"
      }
    },
    {
      "consulta_id": "660e8400-e29b-41d4-a716-446655440001",
      "servicio_id": 1,
      "propiedad_id": 35,
      "monto_deuda": 40000.0,
      "fecha_consulta": "2025-11-15T09:00:00.000Z",
      "metadata": {
        "empresa": "Aguas Andinas",
        "tipo": "Agua"
      },
      "servicios": {
        "tipo_servicio": "Agua",
        "compania": "Aguas Andinas"
      }
    }
  ]
}
```

---

## 4. Listar servicios de una propiedad

### Caso de uso
Ver qué servicios tiene configurados una propiedad antes de consultar deudas.

### Request

```bash
curl http://tu-vps-ip:8000/servicios/propiedad/35
```

### Desde JavaScript

```javascript
const propiedadId = 35;
const response = await fetch(
  `http://tu-vps-ip:8000/servicios/propiedad/${propiedadId}`
);

const data = await response.json();
console.log('Servicios disponibles:', data.servicios);
```

### Response

```json
{
  "propiedad_id": 35,
  "total_servicios": 3,
  "servicios": [
    {
      "servicio_id": 1,
      "propiedad_id": 35,
      "tipo_servicio": "Agua",
      "compania": "Aguas Andinas",
      "credenciales": {
        "numero_cliente": "12345678"
      },
      "activo": true
    },
    {
      "servicio_id": 2,
      "propiedad_id": 35,
      "tipo_servicio": "Luz",
      "compania": "Enel",
      "credenciales": {
        "numero_cliente": "987654321"
      },
      "activo": true
    },
    {
      "servicio_id": 3,
      "propiedad_id": 35,
      "tipo_servicio": "Gas",
      "compania": "Metrogas",
      "credenciales": {
        "numero_cliente": "111222333"
      },
      "activo": true
    }
  ]
}
```

---

## 5. Consultar todas las propiedades (Background)

### Caso de uso
Ejecutar una consulta masiva de todas las propiedades en segundo plano.

### Request

```bash
curl -X POST http://tu-vps-ip:8000/consultar/todas
```

### Response

```json
{
  "mensaje": "Proceso de consulta iniciado en background",
  "nota": "Los resultados se guardarán en la base de datos"
}
```

**Importante**: Esta operación se ejecuta en background. Los resultados se guardan directamente en Supabase y puedes consultarlos después usando el endpoint de historial.

---

## 6. Health check

### Caso de uso
Verificar que la API está funcionando correctamente.

### Request

```bash
curl http://tu-vps-ip:8000/health
```

### Response

```json
{
  "status": "ok",
  "mensaje": "Servicio operativo"
}
```

---

## Flujo de trabajo completo

### Ejemplo: Consultar deudas de múltiples propiedades en paralelo

```javascript
// 1. Obtener servicios de varias propiedades
const propiedadIds = [35, 40, 42];
const serviciosPorPropiedad = [];

for (const propId of propiedadIds) {
  const res = await fetch(`http://tu-vps-ip:8000/servicios/propiedad/${propId}`);
  const data = await res.json();
  serviciosPorPropiedad.push(...data.servicios);
}

// 2. Extraer todos los IDs de servicios
const servicioIds = serviciosPorPropiedad.map(s => s.servicio_id);
console.log('Consultando servicios:', servicioIds);

// 3. Consultar todas las deudas EN PARALELO
const response = await fetch('http://tu-vps-ip:8000/consultar/servicios', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    servicio_ids: servicioIds
  })
});

const resultados = await response.json();

// 4. Calcular totales por propiedad
const deudasPorPropiedad = {};
resultados.resultados.forEach(r => {
  if (!deudasPorPropiedad[r.propiedad_id]) {
    deudasPorPropiedad[r.propiedad_id] = 0;
  }
  deudasPorPropiedad[r.propiedad_id] += r.deuda;
});

console.log('Deudas por propiedad:', deudasPorPropiedad);
// Output: { 35: 57000, 40: 23000, 42: 8000 }
```

---

## Manejo de errores

### Errores comunes

#### 1. Servicio no encontrado (404)

```json
{
  "detail": "Not Found"
}
```

#### 2. Error interno (500)

```json
{
  "detail": "Error consultando servicios: timeout"
}
```

#### 3. Datos inválidos (422)

```json
{
  "detail": [
    {
      "loc": ["body", "servicio_ids"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

### Ejemplo de manejo en JavaScript

```javascript
async function consultarServicios(servicioIds) {
  try {
    const response = await fetch('http://tu-vps-ip:8000/consultar/servicios', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        servicio_ids: servicioIds
      })
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail);
    }

    const data = await response.json();

    // Filtrar solo resultados exitosos
    const exitosos = data.resultados.filter(r => r.exito);
    const fallidos = data.resultados.filter(r => !r.exito);

    console.log(`Exitosos: ${exitosos.length}, Fallidos: ${fallidos.length}`);

    return data;
  } catch (error) {
    console.error('Error consultando servicios:', error.message);
    throw error;
  }
}
```

---

## Performance

### Tiempos de respuesta estimados

- **1 servicio**: ~30 segundos
- **5 servicios (paralelo)**: ~30-40 segundos
- **10 servicios (paralelo)**: ~30-50 segundos

**Ventaja**: El tiempo NO crece linealmente gracias al procesamiento paralelo.

### Recomendaciones

1. **No consultar más de 10 servicios a la vez** para evitar sobrecarga del servidor
2. Si tienes muchos servicios, hacer múltiples requests de 10 en 10
3. Usar el historial para evitar consultas repetidas recientes
4. Configurar un sistema de caché si las consultas son muy frecuentes
