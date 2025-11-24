"""
Script para ejecutar como cron job
Consulta todas las deudas de servicios periódicamente
"""
import asyncio
from batch_processor import BatchProcessor
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('cron_deudas.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


async def ejecutar_cron():
    """
    Función principal del cron job
    Consulta todas las deudas y guarda resultados en Supabase
    """
    logger.info("=" * 80)
    logger.info(f"Iniciando consulta programada de deudas - {datetime.now()}")
    logger.info("=" * 80)

    try:
        processor = BatchProcessor()
        resumen = await processor.procesar_todas_propiedades()
        await processor.close()

        logger.info("=" * 80)
        logger.info("RESUMEN DE EJECUCIÓN:")
        logger.info(f"  Total de servicios: {resumen['total']}")
        logger.info(f"  Consultas exitosas: {resumen['exitosos']}")
        logger.info(f"  Consultas fallidas: {resumen['fallidos']}")
        logger.info("=" * 80)

        # Log de errores si los hubo
        if resumen['fallidos'] > 0:
            logger.warning("SERVICIOS CON ERRORES:")
            for resultado in resumen['resultados']:
                if not resultado['exito']:
                    logger.warning(f"  - Servicio {resultado['servicio_id']}: {resultado['error']}")

        logger.info(f"Consulta programada finalizada - {datetime.now()}")

        return resumen

    except Exception as e:
        logger.error(f"Error crítico en cron job: {str(e)}", exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(ejecutar_cron())
