"""
API REST con FastAPI para consultar deudas de servicios
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional
from batch_processor import BatchProcessor
from database import db
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="API Consulta Deudas Servicios",
    description="API para consultar deudas de servicios básicos de propiedades",
    version="1.0.0"
)


class ConsultaPropiedadRequest(BaseModel):
    propiedad_id: int


class ConsultaServiciosRequest(BaseModel):
    servicio_ids: List[int]


class ConsultaResponse(BaseModel):
    mensaje: str
    job_id: Optional[str] = None


@app.get("/")
async def root():
    """Endpoint raíz"""
    return {
        "mensaje": "API de Consulta de Deudas de Servicios",
        "version": "1.0.0",
        "endpoints": {
            "GET /health": "Verificar estado del servicio",
            "POST /consultar/propiedad": "Consultar deudas de una propiedad",
            "POST /consultar/servicios": "Consultar servicios específicos",
            "POST /consultar/todas": "Consultar todas las propiedades",
            "GET /historial/propiedad/{propiedad_id}": "Ver historial de consultas"
        }
    }


@app.get("/health")
async def health():
    """Health check"""
    return {"status": "ok", "mensaje": "Servicio operativo"}


@app.post("/consultar/propiedad", response_model=dict)
async def consultar_propiedad(request: ConsultaPropiedadRequest):
    """
    Consulta todas las deudas de servicios de una propiedad específica

    Args:
        request: JSON con propiedad_id

    Returns:
        Resultados de las consultas
    """
    try:
        processor = BatchProcessor()
        resultados = await processor.procesar_propiedad(request.propiedad_id)
        await processor.close()

        return {
            "propiedad_id": request.propiedad_id,
            "total_servicios": len(resultados),
            "resultados": resultados
        }

    except Exception as e:
        logger.error(f"Error consultando propiedad {request.propiedad_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/consultar/servicios", response_model=dict)
async def consultar_servicios(request: ConsultaServiciosRequest):
    """
    Consulta deudas de servicios específicos

    Args:
        request: JSON con lista de servicio_ids

    Returns:
        Resultados de las consultas
    """
    try:
        processor = BatchProcessor()
        resultados = await processor.procesar_servicios_especificos(request.servicio_ids)
        await processor.close()

        return {
            "total_servicios": len(resultados),
            "resultados": resultados
        }

    except Exception as e:
        logger.error(f"Error consultando servicios: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/consultar/todas", response_model=dict)
async def consultar_todas_propiedades(background_tasks: BackgroundTasks):
    """
    Consulta todas las propiedades con servicios activos
    Se ejecuta en background para no bloquear la respuesta

    Returns:
        Confirmación de inicio del proceso
    """
    try:
        # Ejecutar en background
        background_tasks.add_task(ejecutar_consulta_completa)

        return {
            "mensaje": "Proceso de consulta iniciado en background",
            "nota": "Los resultados se guardarán en la base de datos"
        }

    except Exception as e:
        logger.error(f"Error iniciando consulta completa: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


async def ejecutar_consulta_completa():
    """Función auxiliar para ejecutar consulta completa en background"""
    try:
        processor = BatchProcessor()
        resumen = await processor.procesar_todas_propiedades()
        await processor.close()
        logger.info(f"Consulta completa finalizada: {resumen}")
    except Exception as e:
        logger.error(f"Error en consulta completa: {str(e)}")


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

    uvicorn.run(
        "api:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True
    )
