"""
Procesador batch para consultar múltiples servicios
"""
import asyncio
from typing import List, Dict
from database import db
from prompt_generator import PromptGenerator
from agent_runner import AgentRunner
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BatchProcessor:
    """
    Procesa múltiples consultas de deuda en batch
    """

    def __init__(self):
        self.agent_runner = AgentRunner()

    async def procesar_servicio(self, servicio: Dict, agent_runner: AgentRunner = None) -> Dict:
        """
        Procesa un servicio individual

        Args:
            servicio: Registro de la tabla 'servicios'
            agent_runner: AgentRunner a usar (para paralelización)

        Returns:
            Dict con resultado de la consulta
        """
        # Usar agent_runner proporcionado o el del batch processor
        runner = agent_runner if agent_runner else self.agent_runner

        try:
            # Obtener información de la empresa
            empresa_info = db.get_empresa_servicio(servicio["compania"])

            if not empresa_info:
                logger.warning(f"No se encontró información para la empresa: {servicio['compania']}")
                return {
                    "servicio_id": servicio["servicio_id"],
                    "propiedad_id": servicio["propiedad_id"],
                    "exito": False,
                    "error": f"Empresa no registrada: {servicio['compania']}"
                }

            # Generar prompt
            prompt = PromptGenerator.generate_prompt_from_servicio(servicio, empresa_info)

            logger.info(f"Consultando servicio {servicio['servicio_id']} - {servicio['compania']}")

            # Ejecutar agente
            resultado = await runner.consultar_deuda(prompt)

            # Guardar en base de datos
            db.guardar_consulta_deuda(
                servicio_id=servicio["servicio_id"],
                propiedad_id=servicio["propiedad_id"],
                monto_deuda=resultado["deuda"],
                metadata={"empresa": servicio["compania"], "tipo": servicio["tipo_servicio"]},
                error=resultado["error"]
            )

            logger.info(f"Servicio {servicio['servicio_id']}: Deuda = ${resultado['deuda']}")

            return {
                "servicio_id": servicio["servicio_id"],
                "propiedad_id": servicio["propiedad_id"],
                "empresa": servicio["compania"],
                "deuda": resultado["deuda"],
                "exito": resultado["error"] is None,
                "error": resultado["error"]
            }

        except Exception as e:
            logger.error(f"Error procesando servicio {servicio['servicio_id']}: {str(e)}")
            return {
                "servicio_id": servicio["servicio_id"],
                "propiedad_id": servicio["propiedad_id"],
                "exito": False,
                "error": str(e)
            }

    async def procesar_propiedad(self, propiedad_id: int) -> List[Dict]:
        """
        Procesa todos los servicios de una propiedad

        Args:
            propiedad_id: ID de la propiedad

        Returns:
            Lista de resultados
        """
        servicios = db.get_servicios_propiedad(propiedad_id)

        if not servicios:
            logger.warning(f"No se encontraron servicios para la propiedad {propiedad_id}")
            return []

        logger.info(f"Procesando {len(servicios)} servicios para propiedad {propiedad_id}")

        # Procesar servicios secuencialmente para evitar sobrecarga
        resultados = []
        for servicio in servicios:
            resultado = await self.procesar_servicio(servicio)
            resultados.append(resultado)
            # Pequeña pausa entre consultas para no saturar el servicio
            await asyncio.sleep(2)

        return resultados

    async def procesar_todas_propiedades(self) -> Dict:
        """
        Procesa todas las propiedades con servicios activos

        Returns:
            Dict con resumen de resultados
        """
        servicios = db.get_todas_propiedades_con_servicios()

        if not servicios:
            logger.warning("No se encontraron servicios activos")
            return {"total": 0, "exitosos": 0, "fallidos": 0, "resultados": []}

        logger.info(f"Iniciando procesamiento de {len(servicios)} servicios")

        resultados = []
        for servicio in servicios:
            resultado = await self.procesar_servicio(servicio)
            resultados.append(resultado)
            # Pausa entre consultas
            await asyncio.sleep(2)

        exitosos = sum(1 for r in resultados if r["exito"])
        fallidos = len(resultados) - exitosos

        resumen = {
            "total": len(resultados),
            "exitosos": exitosos,
            "fallidos": fallidos,
            "resultados": resultados
        }

        logger.info(f"Procesamiento completado: {exitosos}/{len(resultados)} exitosos")

        return resumen

    async def procesar_servicios_especificos(self, servicio_ids: List[int]) -> List[Dict]:
        """
        Procesa una lista específica de servicios en paralelo

        Args:
            servicio_ids: Lista de IDs de servicios

        Returns:
            Lista de resultados
        """
        servicios = db.get_servicios_por_ids(servicio_ids)

        # Crear un AgentRunner independiente para cada servicio (paralelización real)
        async def procesar_con_runner(servicio):
            runner = AgentRunner()
            try:
                resultado = await self.procesar_servicio(servicio, runner)
                return resultado
            finally:
                await runner.close()

        # Procesar servicios en paralelo usando asyncio.gather
        tareas = [procesar_con_runner(servicio) for servicio in servicios]
        resultados = await asyncio.gather(*tareas)

        return list(resultados)

    async def close(self):
        """Cierra recursos"""
        await self.agent_runner.close()
