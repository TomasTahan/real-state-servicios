# Dockerfile para despliegue en Easypanel
FROM python:3.12-slim

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    curl \
    git \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Instalar UV
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Crear directorio de trabajo
WORKDIR /app

# Variables de entorno por defecto (se sobrescriben con .env en Easypanel)
ENV API_HOST=0.0.0.0
ENV API_PORT=8000
ENV BROWSER_USE_CLOUD=true
ENV MAX_FAILURES=3
ENV STEP_TIMEOUT=30
ENV MAX_ACTIONS_PER_STEP=5

# Copiar archivos de dependencias primero (para cache de Docker)
COPY pyproject.toml uv.lock ./

# Instalar dependencias de Python con UV
RUN uv sync --frozen --no-dev

# Copiar el resto del código
COPY . .

# Exponer puerto
EXPOSE 8000

# Comando para iniciar la aplicación con uvicorn directamente
CMD ["uv", "run", "--no-sync", "uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
