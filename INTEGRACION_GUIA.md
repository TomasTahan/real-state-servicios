# Guía de Integración - Sistema de Consulta de Deudas de Servicios

## 📋 Resumen Ejecutivo

Esta aplicación es un **sistema automatizado de consulta de deudas de servicios básicos** (agua, luz, gas, gastos comunes) para propiedades en arriendo. Utiliza **browser-use con IA** para navegar automáticamente los portales de pago (principalmente Servipag) y extraer información de deudas.

**⚡ NUEVA VERSIÓN 2.0**: Ahora incluye **sistema de cola de trabajos** con control de concurrencia para manejar múltiples solicitudes simultáneas de forma eficiente.

## 🏗️ Arquitectura del Sistema

```
┌─────────────────┐
│   API FastAPI   │  ← Consultas bajo demanda vía HTTP
│   (Puerto 8000) │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────┐
│         JobQueue (NUEVO)            │
│  - Cola de trabajos asíncrona       │
│  - Control de concurrencia (3 max)  │
│  - Workers paralelos                │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│     BatchProcessor                  │
│  - Procesa múltiples servicios      │
│  - Maneja paralelización            │
└────────┬─────────────┬──────────────┘
         │             │
         ▼             ▼
┌────────────────┐  ┌──────────────────┐
│  AgentRunner   │  │ PromptGenerator  │
│  - Browser-Use │  │ - Crea prompts   │
│  - Ejecuta IA  │  │   dinámicos      │
└────────────────┘  └──────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│      Supabase Database              │
│  - servicios (config de servicios)  │
│  - propiedades (info propiedades)   │
│  - empresas_servicio (empresas)     │
│  - consultas_deuda (historial)      │
└─────────────────────────────────────┘
```

## 🔄 Sistema de Cola de Trabajos (v2.0)

### ¿Qué es?
Un sistema de cola asíncrona que permite:
- ✅ **Encolar múltiples consultas** sin bloquear el servidor
- ✅ **Control de concurrencia**: máximo 3 trabajos procesándose simultáneamente
- ✅ **Respuesta inmediata**: retorna `job_id` al instante
- ✅ **Consultar estado**: verificar progreso con el `job_id`
- ✅ **Evita sobrecarga**: protege contra 50+ requests simultáneos

### ¿Cómo funciona?

1. **Cliente envía request** → API encola el trabajo y retorna `job_id`
2. **Cliente consulta estado** → `GET /job/{job_id}` para ver el progreso
3. **Workers procesan** → Máximo 3 trabajos en paralelo
4. **Cliente obtiene resultado** → Cuando `status` sea `completed`

## 🔌 API REST - Endpoints Disponibles

### Base URL
```
http://localhost:8000
```

### 1. Health Check
```bash
GET /health
```

**Response:**
```json
{
  "status": "ok",
  "mensaje": "Servicio operativo"
}
```

### 2. Consultar Deudas de una Propiedad (Encolado)
```bash
POST /consultar/propiedad
Content-Type: application/json

{
  "propiedad_id": 35
}
```

**Response Inmediata:**
```json
{
  "job_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": "pending",
  "propiedad_id": 35,
  "mensaje": "Consulta encolada correctamente",
  "nota": "Use GET /job/{job_id} para consultar el estado y resultado"
}
```

**Luego consultar el resultado:**
```bash
GET /job/a1b2c3d4-e5f6-7890-abcd-ef1234567890
```

**Response cuando está completado:**
```json
{
  "job_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "tipo": "propiedad",
  "params": {"propiedad_id": 35},
  "status": "completed",
  "created_at": "2025-01-15T10:00:00",
  "started_at": "2025-01-15T10:00:05",
  "completed_at": "2025-01-15T10:00:35",
  "worker_id": 0,
  "resultado": [
    {
      "servicio_id": 5,
      "propiedad_id": 35,
      "empresa": "Metrogas",
      "deuda": 25670.0,
      "exito": true,
      "error": null
    },
    {
      "servicio_id": 6,
      "propiedad_id": 35,
      "empresa": "Aguas Andinas",
      "deuda": 12340.5,
      "exito": true,
      "error": null
    }
  ],
  "error": null
}
```

### 3. Consultar Servicios Específicos
```bash
POST /consultar/servicios
Content-Type: application/json

{
  "servicio_ids": [5, 8, 12]
}
```

**Response:**
```json
{
  "total_servicios": 3,
  "resultados": [
    {
      "servicio_id": 5,
      "propiedad_id": 35,
      "empresa": "Metrogas",
      "deuda": 25670.0,
      "exito": true,
      "error": null
    }
  ]
}
```

### 4. Consultar Todas las Propiedades (Background)
```bash
POST /consultar/todas
```

**Response:**
```json
{
  "mensaje": "Proceso de consulta iniciado en background",
  "nota": "Los resultados se guardarán en la base de datos"
}
```

### 5. Ver Historial de Consultas
```bash
GET /historial/propiedad/{propiedad_id}?limit=10
```

**Response:**
```json
{
  "propiedad_id": 35,
  "total_registros": 10,
  "historial": [
    {
      "consulta_id": "uuid",
      "servicio_id": 5,
      "monto_deuda": 25670.0,
      "fecha_consulta": "2025-01-15T10:30:00Z",
      "metadata": {
        "empresa": "Metrogas",
        "tipo": "Gas"
      },
      "error": null,
      "servicios": {
        "tipo_servicio": "Gas",
        "compania": "Metrogas"
      }
    }
  ]
}
```

### 6. Listar Servicios de una Propiedad
```bash
GET /servicios/propiedad/{propiedad_id}
```

**Response:**
```json
{
  "propiedad_id": 35,
  "total_servicios": 4,
  "servicios": [
    {
      "servicio_id": 5,
      "propiedad_id": 35,
      "tipo_servicio": "Gas",
      "compania": "Metrogas",
      "credenciales": {
        "identificador": "900728824"
      },
      "activo": true
    }
  ]
}
```

---

## 🆕 Nuevos Endpoints - Sistema de Cola (v2.0)

### 7. Consultar Estado de un Trabajo
```bash
GET /job/{job_id}
```

**Response (pending):**
```json
{
  "job_id": "abc-123",
  "tipo": "propiedad",
  "params": {"propiedad_id": 35},
  "status": "pending",
  "queue_position": 2,
  "created_at": "2025-01-15T10:00:00",
  "started_at": null,
  "completed_at": null,
  "resultado": null,
  "error": null
}
```

**Response (processing):**
```json
{
  "job_id": "abc-123",
  "tipo": "propiedad",
  "params": {"propiedad_id": 35},
  "status": "processing",
  "worker_id": 1,
  "created_at": "2025-01-15T10:00:00",
  "started_at": "2025-01-15T10:00:05",
  "completed_at": null,
  "resultado": null,
  "error": null
}
```

**Response (completed):**
```json
{
  "job_id": "abc-123",
  "tipo": "propiedad",
  "status": "completed",
  "created_at": "2025-01-15T10:00:00",
  "started_at": "2025-01-15T10:00:05",
  "completed_at": "2025-01-15T10:00:35",
  "resultado": [...],
  "error": null
}
```

**Response (failed):**
```json
{
  "job_id": "abc-123",
  "tipo": "propiedad",
  "status": "failed",
  "error": "Error al consultar servicio...",
  "completed_at": "2025-01-15T10:00:20"
}
```

### 8. Listar Todos los Trabajos
```bash
GET /jobs?status=completed&limit=20
```

**Query params:**
- `status` (opcional): `pending`, `processing`, `completed`, `failed`
- `limit` (opcional): máximo de trabajos a retornar (default: 50)

**Response:**
```json
{
  "total": 15,
  "filter": "completed",
  "jobs": [
    {
      "job_id": "abc-123",
      "tipo": "propiedad",
      "status": "completed",
      "created_at": "2025-01-15T10:00:00",
      "completed_at": "2025-01-15T10:00:35"
    },
    ...
  ]
}
```

### 9. Estadísticas de la Cola
```bash
GET /queue/stats
```

**Response:**
```json
{
  "total_jobs": 48,
  "pending": 5,
  "processing": 3,
  "completed": 38,
  "failed": 2,
  "queue_size": 5,
  "max_workers": 3,
  "workers_active": true
}
```

## 🗄️ Estructura de la Base de Datos

### Tabla: `servicios`
Servicios configurados para cada propiedad.

```sql
servicios (
  servicio_id: bigint (PK),
  propiedad_id: bigint (FK → propiedades),
  tipo_servicio: text,           -- "Agua", "Gas", "Luz", "Gastos Comunes"
  compania: text,                -- "Metrogas", "Aguas Andinas", etc.
  credenciales: jsonb,           -- {"identificador": "900728824"}
  activo: boolean,
  created_at: timestamptz
)
```

### Tabla: `empresas_servicio`
Mapeo de empresas a URLs de Servipag.

```sql
empresas_servicio (
  empresa_id: bigserial (PK),
  nombre: text (UNIQUE),         -- "Metrogas", "Aguas Andinas"
  tipo_servicio: text,           -- "Gas", "Agua"
  url_servipag: text,            -- URL completa del portal
  campo_identificador: text,     -- "Número de Cliente", "RUT"
  activo: boolean,
  created_at: timestamptz
)
```

**Empresas pre-cargadas:**
- **Agua**: Aguas Andinas, Essbio, Esval, Nuevosur
- **Gas**: Metrogas, Abastible, Gasco, Lipigas
- **Luz**: Enel, CGE, Chilquinta, Saesa

### Tabla: `consultas_deuda`
Historial de todas las consultas realizadas.

```sql
consultas_deuda (
  consulta_id: uuid (PK),
  servicio_id: bigint (FK → servicios),
  propiedad_id: bigint (FK → propiedades),
  monto_deuda: numeric,
  fecha_consulta: timestamptz,
  metadata: jsonb,
  error: text,
  created_at: timestamptz
)
```

### Tabla: `propiedades`
Información básica de propiedades (debe existir previamente).

```sql
propiedades (
  propiedad_id: bigint (PK),
  calle: text,
  numero: text,
  comuna: text,
  ...
)
```

## 💻 Código de Ejemplo - Cliente HTTP (v2.0 con Cola)

### Python con requests
```python
import requests
import time

BASE_URL = "http://localhost:8000"

def consultar_propiedad(propiedad_id: int, wait_for_result: bool = True):
    """
    Consulta todas las deudas de una propiedad usando el sistema de cola

    Args:
        propiedad_id: ID de la propiedad
        wait_for_result: Si True, espera hasta que el trabajo esté completado

    Returns:
        Resultado completo del trabajo o solo el job_id si wait_for_result=False
    """
    # 1. Encolar el trabajo
    response = requests.post(
        f"{BASE_URL}/consultar/propiedad",
        json={"propiedad_id": propiedad_id}
    )
    job_data = response.json()
    job_id = job_data["job_id"]

    print(f"✓ Trabajo encolado: {job_id}")

    if not wait_for_result:
        return job_data

    # 2. Esperar hasta que esté completado
    while True:
        status_response = requests.get(f"{BASE_URL}/job/{job_id}")
        job = status_response.json()

        status = job["status"]
        print(f"  Estado: {status}", end="")

        if status == "pending":
            print(f" (posición en cola: {job.get('queue_position', '?')})")
        elif status == "processing":
            print(f" (worker: {job.get('worker_id', '?')})")
        elif status == "completed":
            print(" ✓")
            return job["resultado"]
        elif status == "failed":
            print(f" ✗ Error: {job['error']}")
            return None

        time.sleep(2)  # Esperar 2 segundos antes de volver a consultar

def consultar_servicios_especificos(servicio_ids: list[int], wait_for_result: bool = True):
    """Consulta servicios específicos usando el sistema de cola"""
    response = requests.post(
        f"{BASE_URL}/consultar/servicios",
        json={"servicio_ids": servicio_ids}
    )
    job_data = response.json()
    job_id = job_data["job_id"]

    if not wait_for_result:
        return job_data

    while True:
        status_response = requests.get(f"{BASE_URL}/job/{job_id}")
        job = status_response.json()

        if job["status"] == "completed":
            return job["resultado"]
        elif job["status"] == "failed":
            return None

        time.sleep(2)

def get_job_status(job_id: str):
    """Consulta el estado de un trabajo"""
    response = requests.get(f"{BASE_URL}/job/{job_id}")
    return response.json()

def get_queue_stats():
    """Obtiene estadísticas de la cola"""
    response = requests.get(f"{BASE_URL}/queue/stats")
    return response.json()

def ver_historial(propiedad_id: int, limit: int = 10):
    """Ver historial de consultas de una propiedad"""
    response = requests.get(
        f"{BASE_URL}/historial/propiedad/{propiedad_id}?limit={limit}"
    )
    return response.json()

# Ejemplo de uso
if __name__ == "__main__":
    # Consultar deudas de propiedad 35
    print("Consultando propiedad 35...")
    resultados = consultar_propiedad(35, wait_for_result=True)

    if resultados:
        for servicio in resultados:
            if servicio['exito']:
                print(f"{servicio['empresa']}: ${servicio['deuda']:,.2f}")
            else:
                print(f"{servicio['empresa']}: Error - {servicio['error']}")

    # Ver estadísticas de la cola
    print("\nEstadísticas de la cola:")
    stats = get_queue_stats()
    print(f"  Pendientes: {stats['pending']}")
    print(f"  Procesando: {stats['processing']}")
    print(f"  Completados: {stats['completed']}")
    print(f"  Fallidos: {stats['failed']}")
```

### Ejemplo: Enviar múltiples consultas en paralelo
```python
import requests
import time
from concurrent.futures import ThreadPoolExecutor

BASE_URL = "http://localhost:8000"

def encolar_consultas_multiples(propiedad_ids: list[int]):
    """Encola múltiples consultas sin bloquear"""
    job_ids = []

    for prop_id in propiedad_ids:
        response = requests.post(
            f"{BASE_URL}/consultar/propiedad",
            json={"propiedad_id": prop_id}
        )
        job_data = response.json()
        job_ids.append((prop_id, job_data["job_id"]))
        print(f"✓ Propiedad {prop_id} encolada: {job_data['job_id']}")

    return job_ids

def esperar_resultados(job_ids: list[tuple]):
    """Espera y obtiene los resultados de múltiples trabajos"""
    resultados = {}

    # Crear set de jobs pendientes
    pending_jobs = {job_id: prop_id for prop_id, job_id in job_ids}

    while pending_jobs:
        for job_id, prop_id in list(pending_jobs.items()):
            response = requests.get(f"{BASE_URL}/job/{job_id}")
            job = response.json()

            if job["status"] == "completed":
                resultados[prop_id] = job["resultado"]
                del pending_jobs[job_id]
                print(f"✓ Propiedad {prop_id} completada")
            elif job["status"] == "failed":
                resultados[prop_id] = None
                del pending_jobs[job_id]
                print(f"✗ Propiedad {prop_id} falló: {job['error']}")

        if pending_jobs:
            time.sleep(2)

    return resultados

# Ejemplo: Consultar 50 propiedades en paralelo
if __name__ == "__main__":
    propiedades = list(range(1, 51))  # IDs del 1 al 50

    print(f"Encolando {len(propiedades)} consultas...")
    job_ids = encolar_consultas_multiples(propiedades)

    print(f"\nEsperando resultados...")
    resultados = esperar_resultados(job_ids)

    print(f"\n✓ Completado: {len(resultados)} propiedades procesadas")
```

### JavaScript/TypeScript con fetch
```typescript
const BASE_URL = 'http://localhost:8000';

interface ConsultaPropiedadResponse {
  propiedad_id: number;
  total_servicios: number;
  resultados: Array<{
    servicio_id: number;
    propiedad_id: number;
    empresa: string;
    deuda: number;
    exito: boolean;
    error: string | null;
  }>;
}

async function consultarPropiedad(propiedadId: number): Promise<ConsultaPropiedadResponse> {
  const response = await fetch(`${BASE_URL}/consultar/propiedad`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ propiedad_id: propiedadId }),
  });

  return response.json();
}

async function consultarServiciosEspecificos(servicioIds: number[]) {
  const response = await fetch(`${BASE_URL}/consultar/servicios`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ servicio_ids: servicioIds }),
  });

  return response.json();
}

async function verHistorial(propiedadId: number, limit: number = 10) {
  const response = await fetch(
    `${BASE_URL}/historial/propiedad/${propiedadId}?limit=${limit}`
  );

  return response.json();
}

// Ejemplo de uso
(async () => {
  const resultado = await consultarPropiedad(35);
  console.log(`Total servicios: ${resultado.total_servicios}`);

  resultado.resultados.forEach(servicio => {
    if (servicio.exito) {
      console.log(`${servicio.empresa}: $${servicio.deuda.toFixed(2)}`);
    } else {
      console.log(`${servicio.empresa}: Error - ${servicio.error}`);
    }
  });
})();
```

### cURL
```bash
# Health check
curl http://localhost:8000/health

# Consultar propiedad
curl -X POST http://localhost:8000/consultar/propiedad \
  -H "Content-Type: application/json" \
  -d '{"propiedad_id": 35}'

# Consultar servicios específicos
curl -X POST http://localhost:8000/consultar/servicios \
  -H "Content-Type: application/json" \
  -d '{"servicio_ids": [5, 8, 12]}'

# Ver historial
curl http://localhost:8000/historial/propiedad/35?limit=10

# Listar servicios
curl http://localhost:8000/servicios/propiedad/35

# Consultar todas las propiedades (background)
curl -X POST http://localhost:8000/consultar/todas
```

## ⚙️ Variables de Entorno Requeridas

```bash
# Supabase
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=eyJxxx...

# Browser-Use Cloud
BROWSER_USE_CLOUD=true

# Agent settings
MAX_FAILURES=3
STEP_TIMEOUT=30
MAX_ACTIONS_PER_STEP=5

# API settings
API_HOST=0.0.0.0
API_PORT=8000
ENV=production  # o "development"
```

## 🚀 Cómo Iniciar el Servicio

### 1. Con Python directamente
```bash
cd /ruta/al/proyecto
uv run python api.py
```

### 2. Con uvicorn
```bash
uvicorn api:app --host 0.0.0.0 --port 8000
```

### 3. Con systemd (producción)
```bash
sudo systemctl start deudas-api
sudo systemctl status deudas-api
```

## 📊 Flujo de Datos Completo

1. **Cliente hace request** → `POST /consultar/propiedad {"propiedad_id": 35}`

2. **API recibe request** → `api.py:consultar_propiedad()`

3. **BatchProcessor obtiene servicios** → `db.get_servicios_propiedad(35)`
   - Retorna: `[{servicio_id: 5, compania: "Metrogas", credenciales: {...}}]`

4. **Para cada servicio:**
   - **Obtiene info empresa** → `db.get_empresa_servicio("Metrogas")`
     - Retorna: `{url_servipag: "...", campo_identificador: "..."}`

   - **Genera prompt** → `PromptGenerator.generate_prompt_from_servicio()`
     - Retorna: Prompt con instrucciones para el agente IA

   - **Ejecuta agente IA** → `AgentRunner.consultar_deuda(prompt)`
     - Browser-use navega el portal de Servipag
     - Extrae el monto de deuda
     - Retorna: `{"deuda": 25670.0, "error": null}`

   - **Guarda resultado** → `db.guardar_consulta_deuda()`
     - Inserta registro en `consultas_deuda`

5. **API retorna resultados** → JSON con todas las deudas

## 🔧 Componentes Principales

### `api.py` - API REST con FastAPI
- Define todos los endpoints HTTP
- Maneja requests/responses
- Coordina el BatchProcessor

### `batch_processor.py` - Procesador de Servicios
- Procesa múltiples servicios en batch
- Maneja paralelización
- Coordina AgentRunner y Database

### `agent_runner.py` - Ejecutor del Agente IA
- Inicializa browser-use
- Ejecuta prompts con IA
- Extrae resultados estructurados

### `prompt_generator.py` - Generador de Prompts
- Crea prompts dinámicos para cada empresa
- Adapta instrucciones según el portal

### `database.py` - Cliente Supabase
- CRUD operations
- Queries a tablas
- Gestión de conexiones

### `config.py` - Configuración
- Carga variables de entorno
- Settings globales

## 📝 Notas Importantes

### Tiempos de Respuesta
- **Consulta individual**: 15-30 segundos por servicio
- **Múltiples servicios**: Se procesan secuencialmente con pause de 2s entre cada uno
- **Background jobs**: No bloquean la respuesta HTTP

### Limitaciones
- Solo funciona con empresas configuradas en `empresas_servicio`
- Principalmente soporta portal Servipag
- Requiere credenciales correctas en la tabla `servicios`
- Browser-use puede fallar si el portal cambia su estructura

### Manejo de Errores
- Si una consulta falla, retorna `{"deuda": 0, "error": "mensaje"}`
- Los errores se guardan en `consultas_deuda.error`
- El sistema continúa procesando otros servicios aunque uno falle

### Seguridad
- Las credenciales se almacenan en Supabase (encriptado en tránsito)
- No se exponen credenciales en logs
- API sin autenticación (agregar según necesidad)

## 🎯 Casos de Uso Comunes

### 1. Dashboard de Propiedades
```python
# Obtener deudas de todas las propiedades para mostrar en dashboard
propiedades = [35, 36, 37, 38]
deudas_totales = {}

for prop_id in propiedades:
    resultado = requests.post(
        f"{BASE_URL}/consultar/propiedad",
        json={"propiedad_id": prop_id}
    ).json()

    total = sum(r['deuda'] for r in resultado['resultados'] if r['exito'])
    deudas_totales[prop_id] = total

print(deudas_totales)
# {35: 45670.5, 36: 0, 37: 12340, 38: 8900}
```

### 2. Alertas de Deudas Altas
```python
# Verificar propiedades con deudas > $20,000
UMBRAL_DEUDA = 20000

for prop_id in propiedades:
    resultado = consultar_propiedad(prop_id)

    for servicio in resultado['resultados']:
        if servicio['exito'] and servicio['deuda'] > UMBRAL_DEUDA:
            enviar_alerta(
                propiedad=prop_id,
                empresa=servicio['empresa'],
                deuda=servicio['deuda']
            )
```

### 3. Reporte Mensual
```python
# Generar reporte de deudas del mes
from datetime import datetime, timedelta

mes_pasado = datetime.now() - timedelta(days=30)

for prop_id in propiedades:
    historial = ver_historial(prop_id, limit=100)

    deudas_mes = [
        h for h in historial['historial']
        if datetime.fromisoformat(h['fecha_consulta']) > mes_pasado
    ]

    generar_reporte_pdf(prop_id, deudas_mes)
```

## 🔄 Integración con Tu Aplicación

### Paso 1: Verificar Conexión
```python
response = requests.get("http://localhost:8000/health")
if response.json()["status"] == "ok":
    print("✅ API de deudas conectada")
```

### Paso 2: Crear Wrapper/Client
```python
class DeudaServiceClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url

    def consultar_propiedad(self, propiedad_id: int):
        response = requests.post(
            f"{self.base_url}/consultar/propiedad",
            json={"propiedad_id": propiedad_id}
        )
        response.raise_for_status()
        return response.json()

    # ... más métodos

client = DeudaServiceClient()
```

### Paso 3: Integrar en Tu Lógica de Negocio
```python
# En tu aplicación de gestión de propiedades
from deuda_service_client import DeudaServiceClient

deuda_client = DeudaServiceClient()

def obtener_estado_propiedad(propiedad_id: int):
    # Tu lógica existente
    propiedad = db.get_propiedad(propiedad_id)

    # Integrar consulta de deudas
    try:
        deudas = deuda_client.consultar_propiedad(propiedad_id)
        propiedad['deudas_servicios'] = deudas['resultados']
    except Exception as e:
        propiedad['deudas_servicios'] = None
        logger.error(f"Error consultando deudas: {e}")

    return propiedad
```

## 📦 Dependencias del Sistema

```toml
[project]
dependencies = [
    "browser-use>=0.9.7",      # IA para navegación web
    "fastapi>=0.115.0",        # API REST
    "uvicorn>=0.32.0",         # Servidor ASGI
    "supabase>=2.9.0",         # Cliente de base de datos
    "pydantic>=2.9.0",         # Validación de datos
    "pydantic-settings>=2.6.0", # Gestión de settings
    "python-dotenv>=1.0.0",    # Variables de entorno
]
```

## 🆘 Troubleshooting

### Error: "Empresa no registrada"
**Solución**: Agregar empresa a `empresas_servicio`:
```sql
INSERT INTO empresas_servicio (nombre, tipo_servicio, url_servipag, campo_identificador)
VALUES ('NuevaEmpresa', 'Agua', 'https://portal.servipag.com/...', 'Número de Cliente');
```

### Error: Timeout en consultas
**Solución**: Aumentar `STEP_TIMEOUT` en `.env` a 60 o más.

### Error: Deuda retorna 0 cuando hay deuda
**Solución**: El formato del portal cambió. Revisar logs y ajustar prompt en `prompt_generator.py`.

### Error: Connection refused
**Solución**: Verificar que el servicio esté corriendo:
```bash
ps aux | grep "python api.py"
curl http://localhost:8000/health
```

---

## 📞 Resumen para Integración Rápida

**Para integrar esta app en tu aplicación:**

1. **Inicia el servicio**: `uv run python api.py`
2. **Verifica conexión**: `curl http://localhost:8000/health`
3. **Usa el endpoint principal**:
   ```
   POST /consultar/propiedad {"propiedad_id": 35}
   ```
4. **Procesa la respuesta**: JSON con array de `resultados` conteniendo `deuda` por cada servicio

**Endpoints clave:**
- `/consultar/propiedad` - Consulta una propiedad completa
- `/consultar/servicios` - Consulta servicios específicos
- `/historial/propiedad/{id}` - Ver consultas históricas
- `/servicios/propiedad/{id}` - Listar servicios configurados

**Tiempo de respuesta**: 15-30 segundos por servicio consultado.

**Formato de respuesta**:
```json
{
  "resultados": [
    {"servicio_id": 5, "empresa": "Metrogas", "deuda": 25670.0, "exito": true}
  ]
}
```
