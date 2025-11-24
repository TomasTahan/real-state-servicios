"""
Script de prueba para el sistema de cola de trabajos
"""
import requests
import time
from concurrent.futures import ThreadPoolExecutor

BASE_URL = "http://localhost:8000"


def test_health():
    """Prueba el health check"""
    print("🔍 Probando health check...")
    response = requests.get(f"{BASE_URL}/health")
    data = response.json()
    print(f"✓ Health: {data['status']}\n")
    return data['status'] == 'ok'


def test_queue_stats():
    """Prueba las estadísticas de la cola"""
    print("📊 Obteniendo estadísticas de la cola...")
    response = requests.get(f"{BASE_URL}/queue/stats")
    stats = response.json()
    print(f"  Total trabajos: {stats['total_jobs']}")
    print(f"  Pendientes: {stats['pending']}")
    print(f"  Procesando: {stats['processing']}")
    print(f"  Completados: {stats['completed']}")
    print(f"  Fallidos: {stats['failed']}")
    print(f"  Workers activos: {stats['workers_active']}")
    print(f"  Max workers: {stats['max_workers']}\n")
    return stats


def test_single_job():
    """Prueba encolar un solo trabajo"""
    print("🔧 Probando trabajo individual...")

    # Encolar
    response = requests.post(
        f"{BASE_URL}/consultar/propiedad",
        json={"propiedad_id": 35}
    )
    job_data = response.json()
    job_id = job_data["job_id"]
    print(f"✓ Trabajo encolado: {job_id}")

    # Monitorear
    max_attempts = 60
    for attempt in range(max_attempts):
        response = requests.get(f"{BASE_URL}/job/{job_id}")
        job = response.json()
        status = job["status"]

        print(f"  [{attempt+1}/{max_attempts}] Estado: {status}", end="")

        if status == "pending":
            print(f" (posición: {job.get('queue_position', '?')})")
        elif status == "processing":
            print(f" (worker: {job.get('worker_id', '?')})")
        elif status == "completed":
            print(" ✓")
            print(f"  Resultado: {len(job.get('resultado', []))} servicios consultados\n")
            return True
        elif status == "failed":
            print(f" ✗")
            print(f"  Error: {job.get('error', 'Desconocido')}\n")
            return False

        time.sleep(2)

    print("  ⚠️ Timeout esperando resultado\n")
    return False


def test_multiple_jobs(count: int = 5):
    """Prueba encolar múltiples trabajos"""
    print(f"🚀 Probando {count} trabajos en paralelo...")

    # Encolar todos los trabajos
    job_ids = []
    start_time = time.time()

    for i in range(count):
        response = requests.post(
            f"{BASE_URL}/consultar/propiedad",
            json={"propiedad_id": 35}
        )
        job_data = response.json()
        job_ids.append(job_data["job_id"])
        print(f"  [{i+1}/{count}] Encolado: {job_data['job_id'][:8]}...")

    enqueue_time = time.time() - start_time
    print(f"✓ {count} trabajos encolados en {enqueue_time:.2f}s\n")

    # Esperar resultados
    print(f"⏳ Esperando resultados...")
    pending_jobs = set(job_ids)
    completed = 0
    failed = 0

    max_wait = 120  # 2 minutos máximo
    start_wait = time.time()

    while pending_jobs and (time.time() - start_wait) < max_wait:
        for job_id in list(pending_jobs):
            response = requests.get(f"{BASE_URL}/job/{job_id}")
            job = response.json()

            if job["status"] == "completed":
                completed += 1
                pending_jobs.remove(job_id)
                print(f"  ✓ Completado {completed}/{count}: {job_id[:8]}...")
            elif job["status"] == "failed":
                failed += 1
                pending_jobs.remove(job_id)
                print(f"  ✗ Fallido {failed}/{count}: {job_id[:8]}...")

        if pending_jobs:
            time.sleep(2)

    total_time = time.time() - start_time
    print(f"\n📈 Resumen:")
    print(f"  Total: {count} trabajos")
    print(f"  Completados: {completed}")
    print(f"  Fallidos: {failed}")
    print(f"  Pendientes: {len(pending_jobs)}")
    print(f"  Tiempo total: {total_time:.2f}s")
    print(f"  Tiempo promedio por trabajo: {total_time/count:.2f}s\n")

    return completed == count


def test_queue_overload(count: int = 10):
    """Prueba sobrecargar la cola con muchos trabajos"""
    print(f"💥 Probando sobrecarga con {count} trabajos simultáneos...")

    # Encolar todos rápidamente
    def encolar(i):
        response = requests.post(
            f"{BASE_URL}/consultar/propiedad",
            json={"propiedad_id": 35}
        )
        return response.json()["job_id"]

    start_time = time.time()

    with ThreadPoolExecutor(max_workers=10) as executor:
        job_ids = list(executor.map(encolar, range(count)))

    enqueue_time = time.time() - start_time
    print(f"✓ {count} trabajos encolados en {enqueue_time:.2f}s")
    print(f"  Throughput: {count/enqueue_time:.2f} jobs/s\n")

    # Ver estadísticas de la cola
    stats = test_queue_stats()

    return len(job_ids) == count


def main():
    """Ejecuta todas las pruebas"""
    print("=" * 60)
    print("  PRUEBAS DEL SISTEMA DE COLA DE TRABAJOS")
    print("=" * 60)
    print()

    try:
        # 1. Health check
        if not test_health():
            print("❌ API no está respondiendo")
            return

        # 2. Estadísticas iniciales
        test_queue_stats()

        # 3. Trabajo individual
        print("---" * 20)
        if test_single_job():
            print("✅ Prueba de trabajo individual: PASÓ")
        else:
            print("❌ Prueba de trabajo individual: FALLÓ")

        # 4. Múltiples trabajos
        print("---" * 20)
        if test_multiple_jobs(5):
            print("✅ Prueba de múltiples trabajos: PASÓ")
        else:
            print("⚠️ Prueba de múltiples trabajos: COMPLETÓ PARCIALMENTE")

        # 5. Sobrecarga
        print("---" * 20)
        if test_queue_overload(10):
            print("✅ Prueba de sobrecarga: PASÓ")
        else:
            print("❌ Prueba de sobrecarga: FALLÓ")

        # Estadísticas finales
        print("---" * 20)
        print("📊 Estadísticas finales:")
        test_queue_stats()

        print("=" * 60)
        print("  ✅ PRUEBAS COMPLETADAS")
        print("=" * 60)

    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: No se puede conectar a la API")
        print(f"   Asegúrate de que el servidor esté corriendo en {BASE_URL}")
        print(f"   Ejecuta: uv run python api.py")
    except Exception as e:
        print(f"\n❌ ERROR INESPERADO: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
