"""
API REST con FastAPI para consultar deudas de servicios
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks, Query
from pydantic import BaseModel
from typing import List, Optional
from batch_processor import BatchProcessor
from database import db
from job_queue import job_queue
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="API Consulta Deudas Servicios",
    description="API para consultar deudas de servicios básicos de propiedades",
    version="2.0.0"
)


class ConsultaPropiedadRequest(BaseModel):
    propiedad_id: int
    callback_url: Optional[str] = None  # URL donde enviar resultados
    voucher_id: Optional[str] = None     # ID del voucher (para referencia)


class ConsultaServiciosRequest(BaseModel):
    servicio_ids: List[int]
    callback_url: Optional[str] = None  # URL donde enviar resultados
    voucher_id: Optional[str] = None     # ID del voucher (para referencia)


class ConsultaResponse(BaseModel):
    mensaje: str
    job_id: Optional[str] = None


@app.get("/")
async def root():
    """Endpoint raíz"""
    return {
        "mensaje": "API de Consulta de Deudas de Servicios",
        "version": "2.0.0",
        "modo": "Cola de trabajos con control de concurrencia",
        "endpoints": {
            "GET /health": "Verificar estado del servicio",
            "POST /consultar/propiedad": "Consultar deudas de una propiedad (encola el trabajo)",
            "POST /consultar/servicios": "Consultar servicios específicos (encola el trabajo)",
            "POST /consultar/todas": "Consultar todas las propiedades (encola el trabajo)",
            "GET /job/{job_id}": "Ver estado de un trabajo",
            "GET /jobs": "Listar todos los trabajos",
            "GET /queue/stats": "Ver estadísticas de la cola",
            "GET /historial/propiedad/{propiedad_id}": "Ver historial de consultas",
            "GET /servicios/propiedad/{propiedad_id}": "Listar servicios de una propiedad"
        }
    }


@app.get("/health")
async def health():
    """Health check"""
    return {"status": "ok", "mensaje": "Servicio operativo"}


@app.post("/consultar/propiedad", response_model=dict)
async def consultar_propiedad(request: ConsultaPropiedadRequest):
    """
    Encola una consulta de deudas de servicios de una propiedad específica

    Args:
        request: JSON con propiedad_id

    Returns:
        job_id y estado inicial del trabajo
    """
    try:
        # Encolar el trabajo
        job_id = await job_queue.add_job(
            tipo="propiedad",
            params={"propiedad_id": request.propiedad_id},
            callback_url=request.callback_url,
            voucher_id=request.voucher_id
        )

        mensaje = "Consulta encolada correctamente"
        if request.callback_url:
            mensaje += ". Se notificará al callback cuando termine."

        return {
            "job_id": job_id,
            "status": "pending",
            "propiedad_id": request.propiedad_id,
            "mensaje": mensaje,
            "nota": "Use GET /job/{job_id} para consultar el estado y resultado" if not request.callback_url else None
        }

    except Exception as e:
        logger.error(f"Error encolando consulta de propiedad {request.propiedad_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/consultar/servicios", response_model=dict)
async def consultar_servicios(request: ConsultaServiciosRequest):
    """
    Encola una consulta de deudas de servicios específicos

    Args:
        request: JSON con lista de servicio_ids

    Returns:
        job_id y estado inicial del trabajo
    """
    try:
        # Encolar el trabajo
        job_id = await job_queue.add_job(
            tipo="servicios",
            params={"servicio_ids": request.servicio_ids},
            callback_url=request.callback_url,
            voucher_id=request.voucher_id
        )

        mensaje = "Consulta encolada correctamente"
        if request.callback_url:
            mensaje += ". Se notificará al callback cuando termine."

        return {
            "job_id": job_id,
            "status": "pending",
            "total_servicios": len(request.servicio_ids),
            "mensaje": mensaje,
            "nota": "Use GET /job/{job_id} para consultar el estado y resultado" if not request.callback_url else None
        }

    except Exception as e:
        logger.error(f"Error encolando consulta de servicios: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/consultar/todas", response_model=dict)
async def consultar_todas_propiedades():
    """
    Encola una consulta de todas las propiedades con servicios activos

    Returns:
        job_id y estado inicial del trabajo
    """
    try:
        # Encolar el trabajo
        job_id = await job_queue.add_job(
            tipo="todas",
            params={}
        )

        return {
            "job_id": job_id,
            "status": "pending",
            "mensaje": "Consulta de todas las propiedades encolada",
            "nota": "Use GET /job/{job_id} para consultar el estado y resultado"
        }

    except Exception as e:
        logger.error(f"Error encolando consulta completa: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/job/{job_id}")
async def get_job_status(job_id: str):
    """
    Obtiene el estado y resultado de un trabajo

    Args:
        job_id: ID del trabajo

    Returns:
        Información completa del trabajo
    """
    try:
        job = job_queue.get_job_status(job_id)

        if not job:
            raise HTTPException(status_code=404, detail=f"Trabajo {job_id} no encontrado")

        return job

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo estado del job {job_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/jobs")
async def list_jobs(
    status: Optional[str] = Query(None, description="Filtrar por estado: pending, processing, completed, failed"),
    limit: int = Query(50, description="Cantidad máxima de trabajos a retornar")
):
    """
    Lista todos los trabajos

    Args:
        status: Filtrar por estado (opcional)
        limit: Cantidad máxima de trabajos

    Returns:
        Lista de trabajos
    """
    try:
        jobs = job_queue.get_all_jobs(status=status, limit=limit)

        return {
            "total": len(jobs),
            "filter": status,
            "jobs": jobs
        }

    except Exception as e:
        logger.error(f"Error listando trabajos: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/queue/stats")
async def queue_stats():
    """
    Obtiene estadísticas de la cola de trabajos

    Returns:
        Estadísticas de la cola
    """
    try:
        stats = job_queue.get_queue_stats()
        return stats

    except Exception as e:
        logger.error(f"Error obteniendo estadísticas: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/historial/propiedad/{propiedad_id}")
async def historial_propiedad(propiedad_id: int, limit: int = 10):
    """
    Obtiene el historial de consultas de una propiedad

    Args:
        propiedad_id: ID de la propiedad
        limit: Cantidad de registros a retornar

    Returns:
        Historial de consultas
    """
    try:
        historial = db.get_ultimas_consultas_propiedad(propiedad_id, limit)

        return {
            "propiedad_id": propiedad_id,
            "total_registros": len(historial),
            "historial": historial
        }

    except Exception as e:
        logger.error(f"Error obteniendo historial: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/servicios/propiedad/{propiedad_id}")
async def listar_servicios_propiedad(propiedad_id: int):
    """
    Lista todos los servicios activos de una propiedad

    Args:
        propiedad_id: ID de la propiedad

    Returns:
        Lista de servicios
    """
    try:
        servicios = db.get_servicios_propiedad(propiedad_id)

        return {
            "propiedad_id": propiedad_id,
            "total_servicios": len(servicios),
            "servicios": servicios
        }

    except Exception as e:
        logger.error(f"Error listando servicios: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    from config import settings
    import os

    # Usar reload solo en desarrollo local
    is_dev = os.getenv("ENV", "production") == "development"

    uvicorn.run(
        "api:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=is_dev
    )
