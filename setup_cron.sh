#!/bin/bash
# Script para configurar cron job en el servidor

# Este script debe ejecutarse en el VPS

echo "Configurando cron job para consulta de deudas de servicios..."

# Directorio del proyecto
PROJECT_DIR="/home/usuario/real-state-servicios"  # Ajustar según tu instalación

# Crear entrada en crontab
# Ejecutar dos veces al mes: día 1 a las 9 AM y día 15 a las 9 AM
CRON_ENTRY="0 9 1,15 * * cd $PROJECT_DIR && /usr/bin/uv run python cron_job.py >> $PROJECT_DIR/logs/cron.log 2>&1"

# Agregar a crontab si no existe
(crontab -l 2>/dev/null | grep -v "cron_job.py"; echo "$CRON_ENTRY") | crontab -

echo "Cron job configurado exitosamente!"
echo "Se ejecutará los días 1 y 15 de cada mes a las 9:00 AM"
echo ""
echo "Para verificar: crontab -l"
echo "Para ver logs: tail -f $PROJECT_DIR/logs/cron.log"
