from browser_use import Agent, Browser, ChatBrowserUse
import asyncio
from pydantic import BaseModel

class DeudaOutput(BaseModel):
    deuda: float

async def example():
    browser = Browser(
        use_cloud=True,  # Uncomment to use a stealth browser on Browser Use Cloud
    )

    llm = ChatBrowserUse()

    agent = Agent(
        task="""
    Ve a la página https://portal.servipag.com/paymentexpress/category/gas/company/metrogas

    Sigue estos pasos:
    1. Busca el campo de entrada para el número de cliente
    2. Ingresa el número: 900728824
    3. Haz clic en el botón de consulta/búsqueda
    4. Espera a que cargue la información
    5. Extrae el monto de la deuda que aparece en la página
    6. Devuelve SOLO el monto de la deuda en formato: {"deuda": float}
    """,
        llm=llm,
        browser=browser,
        # use_vision=True,  # Habilita visión para leer mejor los elementos de la página
        max_failures=3,  # Permite hasta 3 reintentos antes de fallar
        step_timeout=30,  # 30 segundos por paso (útil si la página carga lento)
        max_actions_per_step=5,  # Permite múltiples acciones por paso
        directly_open_url=True,  # Navega directamente a la URL sin búsquedas
        output_model_schema=DeudaOutput,  # Estructura el output para obtener datos consistentes
        # save_conversation_path="./logs/servipag_session.json",  # Guarda el historial
        # generate_gif=True,  # Genera GIF de la sesión (útil para ver qué falló)
        # final_response_after_failure=True,  # Intenta dar respuesta aunque falle
    )

    history = await agent.run()
    return history

if __name__ == "__main__":
    history = asyncio.run(example())