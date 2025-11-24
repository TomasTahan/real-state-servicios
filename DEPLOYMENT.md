# Guía de Despliegue en VPS

## Requisitos del servidor

- Ubuntu 20.04+ o Debian
- 2GB RAM mínimo (4GB recomendado)
- Python 3.12+
- Puerto 8000 disponible (o el que configures)

## 1. Preparación del servidor

```bash
# Actualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar dependencias
sudo apt install -y python3-pip curl git

# Instalar UV (gestor de paquetes)
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.cargo/env
```

## 2. Clonar proyecto

```bash
cd /opt
sudo git clone <tu-repo-url> real-state-servicios
sudo chown -R $USER:$USER real-state-servicios
cd real-state-servicios
```

## 3. Configurar variables de entorno

```bash
cp .env.example .env
nano .env
```

Completar con:
```bash
# Browser-Use API Key (obtener en https://browser-use.com)
BROWSER_USE_API_KEY=tu-api-key-real

# Supabase Configuration
SUPABASE_URL=https://tu-proyecto.supabase.co
SUPABASE_KEY=tu-supabase-anon-key

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000

# Browser-Use Settings
BROWSER_USE_CLOUD=true
MAX_FAILURES=3
STEP_TIMEOUT=30
MAX_ACTIONS_PER_STEP=5
```

## 4. Instalar dependencias

```bash
uv sync
```

## 5. Configurar como servicio systemd

Crear archivo `/etc/systemd/system/deudas-api.service`:

```bash
sudo nano /etc/systemd/system/deudas-api.service
```

Contenido:
```ini
[Unit]
Description=API Consulta Deudas Servicios
After=network.target

[Service]
Type=simple
User=tu-usuario
WorkingDirectory=/opt/real-state-servicios
Environment="PATH=/home/tu-usuario/.cargo/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=/home/tu-usuario/.cargo/bin/uv run python api.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Reemplazar**:
- `tu-usuario` con tu usuario de Linux

Activar y arrancar servicio:
```bash
sudo systemctl daemon-reload
sudo systemctl enable deudas-api
sudo systemctl start deudas-api
sudo systemctl status deudas-api
```

## 6. Configurar Nginx como reverse proxy (opcional)

```bash
sudo apt install -y nginx

sudo nano /etc/nginx/sites-available/deudas-api
```

Contenido:
```nginx
server {
    listen 80;
    server_name tu-dominio.com;  # O la IP de tu VPS

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Activar sitio:
```bash
sudo ln -s /etc/nginx/sites-available/deudas-api /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## 7. Configurar firewall

```bash
# Si usas Nginx
sudo ufw allow 'Nginx Full'

# Si accedes directamente al puerto 8000
sudo ufw allow 8000

sudo ufw enable
```

## 8. Uso de la API

### Consultar servicios específicos (PARALELO)

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
  ]
}
```

Los montos se guardan automáticamente en la tabla `consultas_deuda` de Supabase.

### Consultar todas las deudas de una propiedad

```bash
curl -X POST http://tu-vps-ip:8000/consultar/propiedad \
  -H "Content-Type: application/json" \
  -d '{"propiedad_id": 35}'
```

### Ver historial de consultas

```bash
curl http://tu-vps-ip:8000/historial/propiedad/35
```

### Health check

```bash
curl http://tu-vps-ip:8000/health
```

## 9. Monitoreo de logs

```bash
# Ver logs del servicio
sudo journalctl -u deudas-api -f

# Ver últimas 100 líneas
sudo journalctl -u deudas-api -n 100
```

## 10. Configurar cron job (opcional)

Para ejecutar consultas programadas:

```bash
chmod +x setup_cron.sh
./setup_cron.sh
```

Verificar:
```bash
crontab -l
```

## Ventajas del procesamiento paralelo

**Antes** (secuencial):
- 5 servicios × 30 segundos = **150 segundos (2.5 minutos)**

**Ahora** (paralelo):
- 5 servicios en paralelo = **~30 segundos**

**Mejora**: 5x más rápido

## Troubleshooting

### Error: "Address already in use"
```bash
sudo lsof -i :8000
sudo kill -9 <PID>
sudo systemctl restart deudas-api
```

### Error de permisos
```bash
sudo chown -R $USER:$USER /opt/real-state-servicios
```

### Ver procesos activos
```bash
ps aux | grep python
```

### Reiniciar servicio
```bash
sudo systemctl restart deudas-api
```

### Actualizar código
```bash
cd /opt/real-state-servicios
git pull
sudo systemctl restart deudas-api
```

## Seguridad adicional (recomendado)

### 1. Usar HTTPS con Let's Encrypt

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d tu-dominio.com
```

### 2. Rate limiting en Nginx

Agregar a `/etc/nginx/sites-available/deudas-api`:

```nginx
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;

server {
    location / {
        limit_req zone=api_limit burst=20;
        # ... resto de configuración
    }
}
```

### 3. Autenticación básica

Agregar a tu API:
```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials.credentials != "tu-token-secreto":
        raise HTTPException(status_code=401, detail="Token inválido")
    return credentials
```

## Monitoreo avanzado (opcional)

Instalar herramientas de monitoreo:
```bash
# Monitoreo de recursos
sudo apt install -y htop

# Monitoreo de procesos
pip install supervisor
```
