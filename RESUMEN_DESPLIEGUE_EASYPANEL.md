# 🚀 Resumen: Despliegue en Easypanel

## ✅ Archivos creados

Los siguientes archivos fueron creados para facilitar el despliegue:

1. **Dockerfile** - Imagen Docker para la aplicación
2. **.dockerignore** - Archivos a excluir del build
3. **docker-compose.yml** - Configuración Docker Compose (opcional)
4. **EASYPANEL_SETUP.md** - Guía completa paso a paso
5. **EASYPANEL_QUICKSTART.md** - Guía rápida en 5 minutos

---

## 📋 Pasos resumidos

### 1️⃣ Subir a GitHub

```bash
git add .
git commit -m "Add Easypanel deployment support"
git push origin main
```

### 2️⃣ Crear en Easypanel

1. Accede a Easypanel: `http://tu-vps-ip:3000`
2. Create Project → Nombre: `deudas-servicios`
3. Create Service → App
4. Source: **GitHub**
5. Repository: **tu-usuario/real-state-servicios**
6. Branch: **main**
7. Build Method: **Dockerfile**

### 3️⃣ Variables de entorno

Agregar en Easypanel → Environment:

```
BROWSER_USE_API_KEY=tu-api-key-real
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=tu-supabase-key-real
API_HOST=0.0.0.0
API_PORT=8000
BROWSER_USE_CLOUD=true
MAX_FAILURES=3
STEP_TIMEOUT=30
MAX_ACTIONS_PER_STEP=5
```

### 4️⃣ Puerto

Networking → Container Port: **8000** → Expose: ✅

### 5️⃣ Deploy

Click **"Deploy"** → Espera 3-5 minutos

### 6️⃣ Obtener URL

Easypanel te dará:
```
https://deudas-servicios-xxxxx.easypanel.host
```

### 7️⃣ Verificar

```bash
curl https://deudas-servicios-xxxxx.easypanel.host/health
```

---

## 🎯 Usar la API

### Consultar servicios en paralelo

```bash
curl -X POST https://tu-url.easypanel.host/consultar/servicios \
  -H "Content-Type: application/json" \
  -d '{
    "servicio_ids": [1, 3, 5, 7, 9]
  }'
```

### Desde JavaScript

```javascript
const API_URL = 'https://tu-url.easypanel.host';

const response = await fetch(`${API_URL}/consultar/servicios`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ servicio_ids: [1, 3, 5, 7, 9] })
});

const data = await response.json();

// Los montos se guardan automáticamente en Supabase
console.log(data.resultados);
```

---

## 💾 ¿Dónde se guardan los datos?

**Automáticamente en Supabase** - Tabla: `consultas_deuda`

Cada request a `/consultar/servicios`:
1. Consulta el portal web con browser-use
2. Extrae el monto de deuda
3. **Guarda en Supabase** con:
   - `servicio_id`
   - `propiedad_id`
   - `monto_deuda`
   - `fecha_consulta`
   - `metadata` (empresa, tipo)

---

## 🔄 Actualizaciones automáticas (CI/CD)

### Activar auto-deploy

En Easypanel → Settings → **Auto Deploy**: ✅

Ahora cada vez que hagas:
```bash
git push origin main
```

Easypanel automáticamente:
1. Detecta el push
2. Rebuilds la imagen Docker
3. Redeploys el contenedor
4. Sin downtime

---

## 🌐 Dominio personalizado (Opcional)

### Configurar

1. Easypanel → Domains → Add Domain
2. Ingresa: `api.tu-dominio.com`
3. En tu proveedor DNS:
   ```
   Type: A
   Name: api
   Value: [IP de tu VPS]
   TTL: 3600
   ```
4. Espera 5-30 min
5. SSL se configura automáticamente con Let's Encrypt

### Usar

```bash
curl https://api.tu-dominio.com/health
```

---

## 📊 Monitoreo

### Ver logs en tiempo real

Easypanel → Tu servicio → **Logs**

### Health check automático

Easypanel → Advanced → Health Check:
```
Path: /health
Port: 8000
Interval: 30s
```

Si falla 3 veces → **Auto-restart**

### Recursos

Dashboard muestra:
- CPU usage
- RAM usage
- Network traffic
- Request count

---

## 🔒 Seguridad (Recomendaciones)

### 1. Variables de entorno

✅ **NUNCA** commitees el archivo `.env` a GitHub
✅ Usa las variables de entorno de Easypanel
✅ El `.gitignore` ya está configurado correctamente

### 2. API Key rotation

Cambia periódicamente:
- `BROWSER_USE_API_KEY`
- `SUPABASE_KEY`

En Easypanel → Environment → Editar → Redeploy

### 3. Rate limiting (Opcional)

Considera agregar middleware en `api.py`:

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/consultar/servicios")
@limiter.limit("10/minute")  # Max 10 requests por minuto
async def consultar_servicios(...):
    ...
```

---

## 🐛 Troubleshooting

### Build falla

1. Ver logs: Easypanel → Build Logs
2. Verificar que el Dockerfile esté correcto
3. Verificar que `uv` se instale correctamente

### Contenedor no arranca

1. Ver logs: Easypanel → Logs
2. Verificar variables de entorno
3. Comunes:
   - Falta `SUPABASE_URL`
   - Falta `BROWSER_USE_API_KEY`
   - Formato incorrecto (sin comillas)

### 502 Bad Gateway

1. Verificar que `API_HOST=0.0.0.0`
2. Verificar que puerto `8000` esté expuesto
3. Ver logs para errores de la app

### Respuesta lenta

1. Verificar recursos: Dashboard
2. Aumentar CPU/RAM si es necesario:
   - Advanced → Resources
   - CPU: 1-2 cores
   - RAM: 2-4GB

---

## 📈 Escalabilidad

### Aumentar recursos

Easypanel → Advanced → Resources:
```
CPU: 2 cores
RAM: 4GB
```

### Múltiples instancias (Load balancing)

Easypanel Pro permite:
- Múltiples réplicas del servicio
- Load balancer automático
- Auto-scaling

---

## 💰 Costos estimados

### VPS (servidor)
- DigitalOcean: $6-12/mes (2GB-4GB RAM)
- Hetzner: €4-8/mes
- Linode: $10-20/mes

### Browser-Use API
- Depende del uso
- Ver pricing en browser-use.com

### Supabase
- Free tier: Hasta 500MB DB + 2GB storage
- Pro: $25/mes (ilimitado)

### Total estimado
**~$15-40/mes** (dependiendo del uso)

---

## 📚 Documentación completa

Para más detalles, ver:

1. **EASYPANEL_QUICKSTART.md** - Guía rápida
2. **EASYPANEL_SETUP.md** - Guía detallada
3. **DEPLOYMENT.md** - Despliegue manual en VPS
4. **EJEMPLOS_USO_API.md** - Ejemplos de uso
5. **RESUMEN_MEJORAS.md** - Cambios y mejoras

---

## ✅ Checklist final

Antes de ir a producción:

- [ ] Código subido a GitHub
- [ ] Variables de entorno configuradas en Easypanel
- [ ] Puerto 8000 expuesto
- [ ] Deploy exitoso
- [ ] Health check responde OK
- [ ] Prueba de consulta funciona
- [ ] (Opcional) Dominio personalizado configurado
- [ ] (Opcional) Auto-deploy activado
- [ ] (Opcional) Monitoreo configurado
- [ ] (Opcional) Backups de Supabase activos

---

## 🎉 ¡Listo para producción!

Tu API de consulta de deudas está:

✅ Desplegada en Easypanel
✅ Funcionando 24/7
✅ Con procesamiento paralelo (5x más rápido)
✅ Guardando datos automáticamente en Supabase
✅ Con SSL/HTTPS automático
✅ Con logs y monitoreo
✅ Lista para recibir requests

---

**Próximos pasos sugeridos**:

1. Integrar la API en tu aplicación principal
2. Configurar dominio personalizado
3. Agregar autenticación si es necesario
4. Configurar notificaciones (email/WhatsApp)
5. Crear dashboard para visualizar deudas

---

**¿Preguntas?** Revisa la documentación completa o los logs en Easypanel.
