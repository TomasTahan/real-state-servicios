"""
Cliente de base de datos Supabase
"""
from supabase import create_client, Client
from config import settings
from typing import List, Dict, Optional
from datetime import datetime


class SupabaseClient:
    def __init__(self):
        self.client: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

    def get_empresa_servicio(self, nombre_empresa: str) -> Optional[Dict]:
        """Obtiene la información de una empresa de servicio por nombre"""
        response = self.client.table("empresas_servicio").select("*").eq("nombre", nombre_empresa).eq("activo", True).execute()
        return response.data[0] if response.data else None

    def get_servicios_propiedad(self, propiedad_id: int) -> List[Dict]:
        """Obtiene todos los servicios activos de una propiedad"""
        response = self.client.table("servicios").select("*").eq("propiedad_id", propiedad_id).eq("activo", True).execute()
        return response.data

    def get_todas_propiedades_con_servicios(self) -> List[Dict]:
        """Obtiene todas las propiedades que tienen servicios activos"""
        response = self.client.table("servicios").select(
            "servicio_id, propiedad_id, tipo_servicio, compania, credenciales, propiedades(propiedad_id, calle, numero, comuna)"
        ).eq("activo", True).execute()
        return response.data

    def guardar_consulta_deuda(
        self,
        servicio_id: int,
        propiedad_id: int,
        monto_deuda: float,
        metadata: Optional[Dict] = None,
        error: Optional[str] = None
    ) -> Dict:
        """Guarda el resultado de una consulta de deuda"""
        data = {
            "servicio_id": servicio_id,
            "propiedad_id": propiedad_id,
            "monto_deuda": monto_deuda,
            "fecha_consulta": datetime.now().isoformat(),
            "metadata": metadata or {},
            "error": error
        }
        response = self.client.table("consultas_deuda").insert(data).execute()
        return response.data[0] if response.data else None

    def get_ultimas_consultas_propiedad(self, propiedad_id: int, limit: int = 10) -> List[Dict]:
        """Obtiene las últimas consultas de deuda de una propiedad"""
        response = self.client.table("consultas_deuda").select(
            "*, servicios(tipo_servicio, compania)"
        ).eq("propiedad_id", propiedad_id).order("fecha_consulta", desc=True).limit(limit).execute()
        return response.data

    def get_servicios_por_ids(self, servicio_ids: List[int]) -> List[Dict]:
        """Obtiene información de servicios por sus IDs"""
        response = self.client.table("servicios").select("*").in_("servicio_id", servicio_ids).execute()
        return response.data


# Singleton instance
db = SupabaseClient()
