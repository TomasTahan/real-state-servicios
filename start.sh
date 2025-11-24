#!/bin/bash
# Script de inicio para producción

exec uvicorn api:app --host 0.0.0.0 --port 8000 --workers 1
