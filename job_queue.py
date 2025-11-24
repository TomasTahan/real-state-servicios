"""
Sistema de cola de trabajos para procesar consultas de deuda de forma controlada
"""
import asyncio
from typing import Dict, Optional, List
from datetime import datetime
import uuid
import logging
import httpx

logger = logging.getLogger(__name__)


class JobQueue:
    """
    Cola de trabajos para procesar consultas de deuda con control de concurrencia
    """

    def __init__(self, max_workers: int = 3):
        """
        Args:
            max_workers: Número máximo de trabajos procesándose simultáneamente
        """
        self.queue = asyncio.Queue()
        self.max_workers = max_workers
        self.jobs: Dict[str, Dict] = {}
        self.workers_started = False
        self._workers = []
        logger.info(f"JobQueue inicializado con {max_workers} workers")

    async def add_job(self, tipo: str, params: Dict, callback_url: Optional[str] = None, voucher_id: Optional[str] = None) -> str:
        """
        Agrega un trabajo a la cola

        Args:
            tipo: Tipo de trabajo ("propiedad", "servicios", "todas")
            params: Parámetros del trabajo (propiedad_id, servicio_ids, etc)
            callback_url: URL donde enviar resultados cuando termine
            voucher_id: ID del voucher (para referencia)

        Returns:
            job_id: ID único del trabajo
        """
        job_id = str(uuid.uuid4())

        self.jobs[job_id] = {
            "job_id": job_id,
            "tipo": tipo,
            "params": params,
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "started_at": None,
            "completed_at": None,
            "resultado": None,
            "error": None,
            "queue_position": self.queue.qsize() + 1,
            "callback_url": callback_url,
            "voucher_id": voucher_id,
            "callback_sent": False,
            "callback_error": None
        }

        await self.queue.put((job_id, tipo, params))
        logger.info(f"Job {job_id} encolado - Tipo: {tipo}, Posición en cola: {self.jobs[job_id]['queue_position']}, Callback: {callback_url is not None}")

        # Iniciar workers si aún no están corriendo
        if not self.workers_started:
            self._start_workers()

        return job_id

    async def _send_callback(self, job_id: str, max_retries: int = 3) -> bool:
        """
        Envía el callback al finalizar un trabajo

        Args:
            job_id: ID del trabajo
            max_retries: Número máximo de reintentos

        Returns:
            True si se envió exitosamente, False si falló
        """
        job = self.jobs.get(job_id)
        if not job or not job.get("callback_url"):
            return False

        callback_url = job["callback_url"]

        # Preparar payload según formato esperado por Next.js
        # Next.js espera solo { resultados: [...] }
        payload = {
            "resultados": job.get("resultado", [])
        }

        logger.info(f"Enviando callback con {len(payload['resultados'])} resultados para job {job_id}")

        # Reintentar con backoff exponencial
        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(callback_url, json=payload)
                    response.raise_for_status()

                logger.info(f"Callback enviado exitosamente para job {job_id} a {callback_url}")
                self.jobs[job_id]["callback_sent"] = True
                self.jobs[job_id]["callback_error"] = None
                return True

            except Exception as e:
                error_msg = f"Intento {attempt + 1}/{max_retries} falló: {str(e)}"
                logger.warning(f"Error enviando callback para job {job_id}: {error_msg}")

                if attempt < max_retries - 1:
                    # Backoff exponencial: 1s, 2s, 4s
                    wait_time = 2 ** attempt
                    await asyncio.sleep(wait_time)
                else:
                    # Último intento falló
                    self.jobs[job_id]["callback_sent"] = False
                    self.jobs[job_id]["callback_error"] = f"Falló después de {max_retries} intentos: {str(e)}"
                    logger.error(f"Callback falló definitivamente para job {job_id}: {str(e)}")

        return False

    def _start_workers(self):
        """Inicia los workers para procesar la cola"""
        if not self.workers_started:
            self.workers_started = True
            for i in range(self.max_workers):
                worker = asyncio.create_task(self._worker(i))
                self._workers.append(worker)
            logger.info(f"{self.max_workers} workers iniciados")

    async def _worker(self, worker_id: int):
        """
        Worker que procesa trabajos de la cola

        Args:
            worker_id: ID del worker
        """
        from batch_processor import BatchProcessor

        logger.info(f"Worker {worker_id} iniciado")

        while True:
            try:
                # Obtener trabajo de la cola
                job_id, tipo, params = await self.queue.get()

                logger.info(f"Worker {worker_id} procesando job {job_id}")

                # Actualizar estado a "processing"
                self.jobs[job_id]["status"] = "processing"
                self.jobs[job_id]["started_at"] = datetime.now().isoformat()
                self.jobs[job_id]["worker_id"] = worker_id

                try:
                    processor = BatchProcessor()

                    # Procesar según tipo
                    if tipo == "propiedad":
                        propiedad_id = params.get("propiedad_id")
                        resultados = await processor.procesar_propiedad(propiedad_id)

                    elif tipo == "servicios":
                        servicio_ids = params.get("servicio_ids")
                        resultados = await processor.procesar_servicios_especificos(servicio_ids)

                    elif tipo == "todas":
                        resultados = await processor.procesar_todas_propiedades()

                    else:
                        raise ValueError(f"Tipo de trabajo no soportado: {tipo}")

                    await processor.close()

                    # Marcar como completado
                    self.jobs[job_id]["status"] = "completed"
                    self.jobs[job_id]["resultado"] = resultados
                    self.jobs[job_id]["completed_at"] = datetime.now().isoformat()

                    logger.info(f"Job {job_id} completado exitosamente por worker {worker_id}")

                    # Enviar callback si está configurado
                    if self.jobs[job_id].get("callback_url"):
                        await self._send_callback(job_id)

                except Exception as e:
                    # Marcar como fallido
                    self.jobs[job_id]["status"] = "failed"
                    self.jobs[job_id]["error"] = str(e)
                    self.jobs[job_id]["completed_at"] = datetime.now().isoformat()

                    logger.error(f"Job {job_id} falló en worker {worker_id}: {str(e)}")

                    # Enviar callback incluso si falló (para notificar el error)
                    if self.jobs[job_id].get("callback_url"):
                        await self._send_callback(job_id)

                finally:
                    self.queue.task_done()

            except Exception as e:
                logger.error(f"Error en worker {worker_id}: {str(e)}")
                await asyncio.sleep(1)  # Evitar loop infinito en caso de error

    def get_job_status(self, job_id: str) -> Optional[Dict]:
        """
        Obtiene el estado de un trabajo

        Args:
            job_id: ID del trabajo

        Returns:
            Información del trabajo o None si no existe
        """
        job = self.jobs.get(job_id)

        if job and job["status"] == "pending":
            # Calcular posición actual en la cola
            pending_jobs = [j for j in self.jobs.values() if j["status"] == "pending"]
            pending_jobs.sort(key=lambda x: x["created_at"])

            for idx, pending_job in enumerate(pending_jobs):
                if pending_job["job_id"] == job_id:
                    job["queue_position"] = idx + 1
                    break

        return job

    def get_all_jobs(self, status: Optional[str] = None, limit: int = 50) -> List[Dict]:
        """
        Obtiene lista de trabajos

        Args:
            status: Filtrar por estado (pending, processing, completed, failed)
            limit: Cantidad máxima de trabajos a retornar

        Returns:
            Lista de trabajos
        """
        jobs = list(self.jobs.values())

        if status:
            jobs = [j for j in jobs if j["status"] == status]

        # Ordenar por fecha de creación (más recientes primero)
        jobs.sort(key=lambda x: x["created_at"], reverse=True)

        return jobs[:limit]

    def get_queue_stats(self) -> Dict:
        """
        Obtiene estadísticas de la cola

        Returns:
            Diccionario con estadísticas
        """
        total_jobs = len(self.jobs)
        pending = sum(1 for j in self.jobs.values() if j["status"] == "pending")
        processing = sum(1 for j in self.jobs.values() if j["status"] == "processing")
        completed = sum(1 for j in self.jobs.values() if j["status"] == "completed")
        failed = sum(1 for j in self.jobs.values() if j["status"] == "failed")

        return {
            "total_jobs": total_jobs,
            "pending": pending,
            "processing": processing,
            "completed": completed,
            "failed": failed,
            "queue_size": self.queue.qsize(),
            "max_workers": self.max_workers,
            "workers_active": self.workers_started
        }

    async def clear_old_jobs(self, hours: int = 24):
        """
        Limpia trabajos completados/fallidos más antiguos que X horas

        Args:
            hours: Horas de antigüedad
        """
        from datetime import timedelta

        cutoff_time = datetime.now() - timedelta(hours=hours)
        removed = 0

        for job_id, job in list(self.jobs.items()):
            if job["status"] in ["completed", "failed"]:
                completed_at = datetime.fromisoformat(job["completed_at"])
                if completed_at < cutoff_time:
                    del self.jobs[job_id]
                    removed += 1

        logger.info(f"Limpiados {removed} trabajos antiguos (>{hours}h)")
        return removed


# Singleton instance
job_queue = JobQueue(max_workers=3)
