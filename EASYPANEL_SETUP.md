# Guía de Despliegue en Easypanel

## Opción 1: Despliegue desde GitHub (Recomendado)

### Paso 1: Preparar repositorio

```bash
# 1. Asegurarte de tener todos los archivos
git add .
git commit -m "Add Easypanel support with Dockerfile"
git push origin main
```

### Paso 2: Crear proyecto en Easypanel

1. Accede a tu panel de Easypanel: `http://tu-vps-ip:3000` (o el puerto que uses)
2. Click en **"Create Project"**
3. Nombre del proyecto: `deudas-servicios`

### Paso 3: Crear servicio desde GitHub

1. Dentro del proyecto, click en **"Create Service"**
2. Selecciona **"App"**
3. Configuración:
   - **Source**: GitHub
   - **Repository**: Selecciona tu repositorio
   - **Branch**: `main` (o la que uses)
   - **Build Method**: Dockerfile
   - **Dockerfile Path**: `Dockerfile` (por defecto)

### Paso 4: Configurar variables de entorno

En la sección **"Environment Variables"** de Easypanel, agrega:

```
BROWSER_USE_API_KEY=tu-browser-use-api-key-real
SUPABASE_URL=https://tu-proyecto.supabase.co
SUPABASE_KEY=tu-supabase-anon-key-real
API_HOST=0.0.0.0
API_PORT=8000
BROWSER_USE_CLOUD=true
MAX_FAILURES=3
STEP_TIMEOUT=30
MAX_ACTIONS_PER_STEP=5
```

**Importante**:
- Usa las variables **sin** comillas
- Reemplaza los valores de ejemplo con tus credenciales reales

### Paso 5: Configurar puerto

1. En **"Ports"** o **"Networking"**:
   - **Container Port**: `8000`
   - **Protocol**: HTTP
   - **Public**: ✅ Activado

2. Easypanel generará automáticamente:
   - Un dominio: `https://deudas-servicios-xxxxx.easypanel.host`
   - O puedes configurar tu dominio personalizado

### Paso 6: Deploy

1. Click en **"Deploy"**
2. Easypanel hará:
   - Clone del repositorio
   - Build de la imagen Docker
   - Deploy del contenedor
   - Configuración de red

3. Espera 2-5 minutos (primera vez puede tardar más)

### Paso 7: Verificar

```bash
# Verifica que esté funcionando
curl https://deudas-servicios-xxxxx.easypanel.host/health

# Deberías recibir:
# {"status":"ok","mensaje":"Servicio operativo"}
```

---

## Opción 2: Despliegue manual con Docker

### Paso 1: Construir imagen

```bash
# En tu máquina local
docker build -t deudas-servicios:latest .
```

### Paso 2: Subir a Docker Hub (opcional)

```bash
docker tag deudas-servicios:latest tu-usuario/deudas-servicios:latest
docker push tu-usuario/deudas-servicios:latest
```

### Paso 3: Crear servicio en Easypanel

1. **Create Service** → **App**
2. **Source**: Docker Image
3. **Image**: `tu-usuario/deudas-servicios:latest`
4. Configurar variables de entorno (mismo que Opción 1)
5. Configurar puerto: `8000`
6. **Deploy**

---

## Opción 3: Despliegue con Docker Compose (Avanzado)

Si prefieres usar Docker Compose en Easypanel:

### docker-compose.yml

```yaml
version: '3.8'

services:
  api:
    build: .
    container_name: deudas-servicios-api
    restart: always
    ports:
      - "8000:8000"
    environment:
      - BROWSER_USE_API_KEY=${BROWSER_USE_API_KEY}
      - SUPABASE_URL=${SUPABASE_URL}
      - SUPABASE_KEY=${SUPABASE_KEY}
      - API_HOST=0.0.0.0
      - API_PORT=8000
      - BROWSER_USE_CLOUD=true
      - MAX_FAILURES=3
      - STEP_TIMEOUT=30
      - MAX_ACTIONS_PER_STEP=5
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

En Easypanel:
1. **Create Service** → **App**
2. **Source**: GitHub
3. **Build Method**: Docker Compose
4. Agregar variables de entorno
5. **Deploy**

---

## Configuración adicional en Easypanel

### 1. Dominio personalizado

1. En tu servicio, ve a **"Domains"**
2. Click en **"Add Domain"**
3. Ingresa: `api.tu-dominio.com`
4. Easypanel te dará instrucciones para configurar DNS:
   ```
   Type: A
   Name: api
   Value: IP-de-tu-vps
   ```
5. Espera propagación DNS (5-30 min)

### 2. SSL/HTTPS automático

Easypanel configura Let's Encrypt automáticamente:
- ✅ Se activa solo al agregar dominio personalizado
- 🔄 Renovación automática cada 90 días

### 3. Logs

Ver logs en tiempo real:
1. En tu servicio, click en **"Logs"**
2. O desde terminal:
   ```bash
   # SSH a tu VPS
   docker logs -f easypanel-deudas-servicios-api
   ```

### 4. Recursos

Configurar límites de CPU/RAM:
1. **"Advanced"** → **"Resources"**
2. Configuración recomendada:
   ```
   CPU: 1 core
   RAM: 2GB
   ```

### 5. Auto-deploy (CI/CD)

Easypanel puede auto-deployar cuando haces push a GitHub:

1. En tu servicio, **"Settings"**
2. **"Auto Deploy"**: ✅ Activado
3. Ahora cada `git push` rebuildeará automáticamente

---

## Uso de la API desplegada

Una vez desplegado, tu API estará en:

```
https://deudas-servicios-xxxxx.easypanel.host
```

O tu dominio personalizado:
```
https://api.tu-dominio.com
```

### Ejemplo de uso

```bash
# Consultar servicios en paralelo
curl -X POST https://api.tu-dominio.com/consultar/servicios \
  -H "Content-Type: application/json" \
  -d '{
    "servicio_ids": [1, 3, 5, 7, 9]
  }'
```

### Desde JavaScript

```javascript
const API_URL = 'https://api.tu-dominio.com';

const response = await fetch(`${API_URL}/consultar/servicios`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ servicio_ids: [1, 3, 5, 7, 9] })
});

const data = await response.json();
console.log(data);
```

---

## Troubleshooting

### Build falla

**Error**: `uv: command not found`

**Solución**: Verifica que el Dockerfile tenga:
```dockerfile
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.cargo/bin:${PATH}"
```

### Contenedor se detiene inmediatamente

**Causa**: Variables de entorno faltantes

**Solución**: Verifica que hayas agregado:
- `SUPABASE_URL`
- `SUPABASE_KEY`
- `BROWSER_USE_API_KEY`

Ver logs:
```bash
docker logs easypanel-deudas-servicios-api
```

### Puerto no accesible

**Causa**: Puerto no expuesto

**Solución**:
1. En Easypanel: **Networking** → Verifica que el puerto `8000` esté público
2. Firewall del VPS:
   ```bash
   sudo ufw allow 8000
   ```

### Error 502 Bad Gateway

**Causa**: La aplicación no está escuchando en `0.0.0.0`

**Solución**: Verifica en Easypanel que `API_HOST=0.0.0.0`

---

## Actualizar la aplicación

### Desde GitHub (con auto-deploy)

```bash
# Hacer cambios en tu código
git add .
git commit -m "Update feature X"
git push origin main

# Easypanel rebuildeará automáticamente
```

### Manualmente

1. En Easypanel, ve a tu servicio
2. Click en **"Redeploy"**
3. Espera el rebuild

---

## Monitoreo

### Ver uso de recursos

En Easypanel:
1. Dashboard del servicio
2. Gráficas de CPU, RAM, Network

### Health check

Easypanel puede monitorear automáticamente:

1. **"Advanced"** → **"Health Check"**
2. Configurar:
   ```
   Path: /health
   Port: 8000
   Interval: 30s
   ```

Si falla 3 veces seguidas, Easypanel reinicia automáticamente el contenedor.

---

## Costos

Easypanel en sí es **gratis** (self-hosted).

Costos externos:
- VPS: Depende del proveedor ($5-20/mes)
- Browser-Use API: Depende del plan
- Supabase: Free tier disponible

---

## Comandos útiles

```bash
# Ver contenedores de Easypanel
docker ps | grep easypanel

# Ver logs
docker logs -f easypanel-deudas-servicios-api

# Entrar al contenedor
docker exec -it easypanel-deudas-servicios-api bash

# Reiniciar servicio
# (Desde Easypanel UI o)
docker restart easypanel-deudas-servicios-api

# Ver uso de recursos
docker stats easypanel-deudas-servicios-api
```

---

## Checklist de despliegue

- [ ] Código subido a GitHub
- [ ] Dockerfile y .dockerignore creados
- [ ] Variables de entorno configuradas en Easypanel
- [ ] Puerto 8000 expuesto como público
- [ ] Deploy exitoso (sin errores en logs)
- [ ] Health check responde: `curl https://tu-dominio.com/health`
- [ ] Test de consulta funciona
- [ ] (Opcional) Dominio personalizado configurado
- [ ] (Opcional) Auto-deploy activado

---

## Ventajas de Easypanel

✅ **UI amigable** - No necesitas saber Docker commands
✅ **SSL automático** - Let's Encrypt integrado
✅ **Auto-deploy** - CI/CD integrado con GitHub
✅ **Logs centralizados** - Fácil debugging
✅ **Health checks** - Auto-restart si falla
✅ **Escalable** - Fácil ajustar recursos

---

## Próximos pasos

Una vez desplegado:

1. **Probar la API** con Postman o cURL
2. **Configurar dominio personalizado** para producción
3. **Activar auto-deploy** para CI/CD
4. **Configurar monitoreo** con health checks
5. **Agregar autenticación** (JWT) si es necesario
6. **Configurar backups** de Supabase

¡Listo! Tu API estará disponible 24/7 en Easypanel.
