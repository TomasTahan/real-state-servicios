# Quickstart - Easypanel en 5 minutos ⚡

## Paso 1: Subir código a GitHub

```bash
git add .
git commit -m "Add Docker support for Easypanel"
git push origin main
```

---

## Paso 2: Crear proyecto en Easypanel

1. Abre Easypanel: `http://tu-vps-ip:3000`
2. Click **"+ Create Project"**
3. Nombre: `deudas-servicios`

---

## Paso 3: Crear servicio

1. Dentro del proyecto, click **"+ Create Service"**
2. Selecciona **"App"**
3. Configuración:

```
Source: GitHub
Repository: tu-usuario/real-state-servicios
Branch: main
Build Method: Dockerfile
```

---

## Paso 4: Variables de entorno

Click en **"Environment"** y agrega:

```bash
BROWSER_USE_API_KEY=tu-api-key
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=tu-supabase-key
API_HOST=0.0.0.0
API_PORT=8000
BROWSER_USE_CLOUD=true
MAX_FAILURES=3
STEP_TIMEOUT=30
MAX_ACTIONS_PER_STEP=5
```

**Importante**: Sin comillas, valores reales.

---

## Paso 5: Configurar puerto

1. Ve a **"Networking"** o **"Ports"**
2. Configurar:
   ```
   Container Port: 8000
   Protocol: HTTP
   Expose to internet: ✅
   ```

---

## Paso 6: Deploy

1. Click **"Deploy"**
2. Espera 3-5 minutos
3. Easypanel te dará una URL:
   ```
   https://deudas-servicios-xxxxx.easypanel.host
   ```

---

## Paso 7: Verificar

```bash
curl https://deudas-servicios-xxxxx.easypanel.host/health
```

Respuesta esperada:
```json
{"status":"ok","mensaje":"Servicio operativo"}
```

---

## Paso 8: Probar API

```bash
curl -X POST https://deudas-servicios-xxxxx.easypanel.host/consultar/servicios \
  -H "Content-Type: application/json" \
  -d '{"servicio_ids": [5]}'
```

---

## ✅ ¡Listo!

Tu API está desplegada y funcionando 24/7.

**URL de tu API**: La que Easypanel te generó o tu dominio personalizado.

---

## Opcional: Dominio personalizado

1. En tu servicio, **"Domains"**
2. **"+ Add Domain"**
3. Ingresa: `api.tu-dominio.com`
4. Configura DNS:
   ```
   Type: A
   Name: api
   Value: IP-de-tu-vps
   ```
5. Espera 5-30 min
6. Easypanel configurará SSL automáticamente

---

## Opcional: Auto-deploy (CI/CD)

1. **"Settings"** → **"Auto Deploy"**: ✅
2. Ahora cada `git push` rebuildeará automáticamente

```bash
# Hacer cambios
git add .
git commit -m "Update"
git push origin main

# Easypanel rebuildeará solo
```

---

## Ver logs

En Easypanel:
1. Tu servicio → **"Logs"**
2. Logs en tiempo real

---

## Resumen de archivos necesarios

- ✅ `Dockerfile` - Creado
- ✅ `.dockerignore` - Creado
- ✅ `docker-compose.yml` - Creado (opcional)
- ✅ Código en GitHub

---

## Troubleshooting rápido

### Build falla
**Ver logs** en Easypanel → "Build Logs"

### Contenedor no arranca
**Verificar** variables de entorno (SUPABASE_URL, BROWSER_USE_API_KEY, etc.)

### 502 Bad Gateway
**Verificar** que API_HOST=0.0.0.0 y puerto 8000 esté expuesto

### Logs vacíos
**Esperar** 1-2 minutos después del deploy inicial

---

## Próximos pasos

1. ✅ API funcionando
2. 🔧 Configurar dominio personalizado
3. 🔄 Activar auto-deploy
4. 📊 Configurar monitoreo
5. 🔒 Agregar autenticación (si necesitas)

---

**Documentación completa**: Ver `EASYPANEL_SETUP.md`
