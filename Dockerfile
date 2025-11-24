# Dockerfile para despliegue en Easypanel
FROM python:3.12-slim

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Instalar UV
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.cargo/bin:${PATH}"

# Crear directorio de trabajo
WORKDIR /app

# Copiar archivos del proyecto
COPY . .

# Instalar dependencias de Python con UV
RUN uv sync

# Exponer puerto
EXPOSE 8000

# Variables de entorno por defecto (se sobrescriben con .env en Easypanel)
ENV API_HOST=0.0.0.0
ENV API_PORT=8000
ENV BROWSER_USE_CLOUD=true
ENV MAX_FAILURES=3
ENV STEP_TIMEOUT=30
ENV MAX_ACTIONS_PER_STEP=5

# Comando para iniciar la aplicación
CMD ["uv", "run", "python", "api.py"]
