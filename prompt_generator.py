"""
Generador dinámico de prompts para consultar deudas de servicios
"""
from typing import Dict


class PromptGenerator:
    """
    Genera prompts dinámicos basados en la empresa y el identificador del servicio
    """

    @staticmethod
    def generate_prompt(url: str, identificador: str, campo_identificador: str) -> str:
        """
        Genera un prompt para el agente browser-use

        Args:
            url: URL del portal de Servipag
            identificador: Número de cliente/RUT
            campo_identificador: Nombre del campo (ej: "Número de Cliente")

        Returns:
            Prompt formateado para el agente
        """
        prompt = f"""
    Ve a la página {url}

    Sigue estos pasos:
    1. Busca el campo de entrada para el {campo_identificador}
    2. Ingresa el número: {identificador}
    3. Haz clic en el botón de consulta/búsqueda (puede decir "Continuar", "Consultar", "Buscar", etc.)
    4. Espera a que cargue la información
    5. Extrae el monto de la deuda que aparece en la página
    6. Si hay múltiples deudas, suma el total
    7. Si no hay deuda, devuelve 0
    8. Devuelve SOLO el monto de la deuda en formato: {{"deuda": float}}

    IMPORTANTE:
    - El monto debe ser un número (sin símbolos de moneda)
    - Si el monto tiene punto como separador de miles (ej: 4.713), conviértelo correctamente (4713)
    - Si el monto tiene coma decimal (ej: 4.713,50), conviértelo a punto decimal (4713.5)
    """
        return prompt.strip()

    @staticmethod
    def generate_prompt_from_servicio(servicio: Dict, empresa_info: Dict) -> str:
        """
        Genera prompt desde un registro de servicio y empresa

        Args:
            servicio: Registro de la tabla 'servicios'
            empresa_info: Registro de la tabla 'empresas_servicio'

        Returns:
            Prompt formateado
        """
        # Obtener identificador desde credenciales
        identificador = servicio.get("credenciales", {}).get("identificador", "")

        return PromptGenerator.generate_prompt(
            url=empresa_info["url_servipag"],
            identificador=identificador,
            campo_identificador=empresa_info["campo_identificador"]
        )
