# Changelog

## [v2.0.0] - Procesamiento Paralelo

### Mejoras principales

#### ✨ Procesamiento paralelo de servicios
- **Antes**: Los servicios se procesaban uno por uno (secuencial)
- **Ahora**: Los servicios se procesan todos a la vez (paralelo)
- **Beneficio**: 5x más rápido

**Ejemplo**:
```
Antes: 5 servicios × 30s = 150s (2.5 minutos)
Ahora: 5 servicios en paralelo = ~30s
```

### Cambios técnicos

#### `batch_processor.py`
- Modificado `procesar_servicios_especificos()` para usar `asyncio.gather()`
- Cada servicio ahora tiene su propio `AgentRunner` independiente
- Eliminado el `await asyncio.sleep(2)` entre servicios en modo paralelo
- Se mantiene el procesamiento secuencial para `procesar_propiedad()` y `procesar_todas_propiedades()` para evitar sobrecarga

### Archivos nuevos

#### `DEPLOYMENT.md`
Guía completa de despliegue en VPS incluyendo:
- Instalación de dependencias
- Configuración de systemd
- Configuración de Nginx como reverse proxy
- Configuración de firewall
- Monitoreo de logs
- Troubleshooting

#### `EJEMPLOS_USO_API.md`
Ejemplos prácticos de uso de la API:
- Consultar servicios específicos en paralelo
- Consultar todas las deudas de una propiedad
- Ver historial de consultas
- Ejemplos en Bash, JavaScript y Python
- Manejo de errores
- Flujos de trabajo completos

### Uso

#### API REST - Consultar servicios en paralelo

```bash
curl -X POST http://tu-vps-ip:8000/consultar/servicios \
  -H "Content-Type: application/json" \
  -d '{
    "servicio_ids": [1, 3, 5, 7, 9]
  }'
```

**Response**:
```json
{
  "total_servicios": 5,
  "resultados": [
    {
      "servicio_id": 1,
      "empresa": "Aguas Andinas",
      "deuda": 45000.0,
      "exito": true
    },
    ...
  ]
}
```

Los montos se guardan automáticamente en Supabase (`consultas_deuda` table).

### Compatibilidad

- ✅ Todos los endpoints existentes siguen funcionando igual
- ✅ No hay breaking changes
- ✅ Base de datos compatible sin migraciones necesarias

### Próximos pasos sugeridos

1. Implementar rate limiting para evitar abuse
2. Agregar autenticación JWT a los endpoints
3. Implementar caché de consultas (Redis)
4. Dashboard web para visualizar deudas
5. Notificaciones automáticas cuando hay deudas

---

## [v1.0.0] - Versión Inicial

### Características
- Consulta automatizada de deudas via browser-use
- API REST con FastAPI
- Almacenamiento en Supabase
- Procesamiento batch (secuencial)
- Soporte para múltiples empresas (Aguas Andinas, Enel, Metrogas, etc.)
