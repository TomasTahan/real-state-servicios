"""
Ejecutor del agente browser-use para consultar deudas
"""
from browser_use import Agent, Browser, ChatBrowserUse
from pydantic import BaseModel
from config import settings
from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)


class DeudaOutput(BaseModel):
    deuda: float


class AgentRunner:
    """
    Ejecuta el agente browser-use para consultar una deuda
    """

    def __init__(self):
        self.browser = None
        self.llm = None

    async def initialize(self):
        """Inicializa el browser y el LLM"""
        if not self.browser:
            self.browser = Browser(use_cloud=settings.BROWSER_USE_CLOUD)
        if not self.llm:
            self.llm = ChatBrowserUse()

    async def consultar_deuda(self, prompt: str) -> Dict:
        """
        Ejecuta el agente para consultar una deuda

        Args:
            prompt: Prompt generado con la información del servicio

        Returns:
            Dict con 'deuda' (float) y 'error' (str) si hubo error
        """
        await self.initialize()

        try:
            agent = Agent(
                task=prompt,
                llm=self.llm,
                browser=self.browser,
                max_failures=settings.MAX_FAILURES,
                step_timeout=settings.STEP_TIMEOUT,
                max_actions_per_step=settings.MAX_ACTIONS_PER_STEP,
                directly_open_url=True,
                output_model_schema=DeudaOutput,
            )

            history = await agent.run()

            # Obtener el resultado final del historial
            # Browser-use retorna un AgentHistory que tiene el método final_result()
            if history:
                try:
                    final_data = history.final_result()
                    logger.info(f"Final data type: {type(final_data)}")
                    logger.info(f"Final data: {final_data}")

                    # El resultado puede ser:
                    # 1. Un string JSON que necesita parsing
                    if isinstance(final_data, str):
                        import json
                        try:
                            parsed_data = json.loads(final_data)
                            if isinstance(parsed_data, dict) and 'deuda' in parsed_data:
                                logger.info(f"Deuda extraída (JSON string): {parsed_data['deuda']}")
                                return {"deuda": float(parsed_data['deuda']), "error": None}
                        except json.JSONDecodeError:
                            logger.error(f"No se pudo parsear JSON: {final_data}")

                    # 2. Un dict directo
                    elif isinstance(final_data, dict) and 'deuda' in final_data:
                        logger.info(f"Deuda extraída (dict): {final_data['deuda']}")
                        return {"deuda": float(final_data['deuda']), "error": None}

                    # 3. Un Pydantic model
                    elif hasattr(final_data, 'model_dump'):
                        model_dict = final_data.model_dump()
                        logger.info(f"Model dict: {model_dict}")
                        if 'deuda' in model_dict:
                            logger.info(f"Deuda extraída (model): {model_dict['deuda']}")
                            return {"deuda": float(model_dict['deuda']), "error": None}

                    # 4. Acceso directo al atributo
                    elif hasattr(final_data, 'deuda'):
                        logger.info(f"Deuda extraída (attr): {final_data.deuda}")
                        return {"deuda": float(final_data.deuda), "error": None}

                except Exception as inner_e:
                    logger.error(f"Error procesando resultado: {str(inner_e)}")
                    import traceback
                    traceback.print_exc()

            return {"deuda": 0, "error": "No se pudo obtener resultado del agente"}

        except Exception as e:
            logger.error(f"Error al consultar deuda: {str(e)}")
            return {"deuda": 0, "error": str(e)}

    async def close(self):
        """Cierra el browser"""
        # El browser se cierra automáticamente al finalizar el agente
        pass
