"""
Script de prueba para el sistema de callbacks
"""
import requests
import time
from fastapi import FastAPI, Request
import uvicorn
import threading
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_URL = "http://localhost:8000"
CALLBACK_PORT = 9000
CALLBACK_URL = f"http://localhost:{CALLBACK_PORT}/callback"

# Servidor de callback para recibir notificaciones
app = FastAPI()
received_callbacks = []


@app.post("/callback")
async def receive_callback(request: Request):
    """Endpoint que recibe los callbacks del agente"""
    body = await request.json()
    logger.info(f"📩 Callback recibido: {body}")
    received_callbacks.append(body)
    return {"status": "ok", "mensaje": "Callback recibido"}


def start_callback_server():
    """Inicia el servidor de callbacks en un thread separado"""
    uvicorn.run(app, host="0.0.0.0", port=CALLBACK_PORT, log_level="warning")


def test_callback_propiedad():
    """Prueba el sistema de callbacks con una propiedad"""
    print("\n" + "=" * 70)
    print("  TEST 1: Callback para consulta de propiedad")
    print("=" * 70)

    # Limpiar callbacks previos
    received_callbacks.clear()

    # Encolar consulta con callback
    print(f"\n1️⃣  Encolando consulta de propiedad con callback...")
    response = requests.post(
        f"{BASE_URL}/consultar/propiedad",
        json={
            "propiedad_id": 35,
            "callback_url": CALLBACK_URL,
            "voucher_id": "test-voucher-123"
        }
    )

    if response.status_code != 200:
        print(f"❌ Error: {response.status_code} - {response.text}")
        return False

    job_data = response.json()
    job_id = job_data["job_id"]
    print(f"✅ Job encolado: {job_id}")
    print(f"   Mensaje: {job_data['mensaje']}")

    # Esperar a recibir el callback
    print(f"\n2️⃣  Esperando callback (máximo 3 minutos)...")
    max_wait = 180  # 3 minutos
    start_time = time.time()

    while (time.time() - start_time) < max_wait:
        if len(received_callbacks) > 0:
            print(f"✅ Callback recibido después de {time.time() - start_time:.1f}s")
            break
        time.sleep(2)
        print(".", end="", flush=True)
    else:
        print(f"\n❌ No se recibió callback después de {max_wait}s")
        return False

    # Verificar el callback recibido
    print(f"\n3️⃣  Verificando contenido del callback...")
    callback = received_callbacks[0]

    checks = {
        "job_id existe": "job_id" in callback,
        "voucher_id correcto": callback.get("voucher_id") == "test-voucher-123",
        "status existe": "status" in callback,
        "resultados existen": "resultados" in callback,
        "resultados es lista": isinstance(callback.get("resultados"), list),
    }

    all_passed = True
    for check, passed in checks.items():
        status = "✅" if passed else "❌"
        print(f"   {status} {check}")
        if not passed:
            all_passed = False

    # Verificar estructura de los resultados
    if callback.get("resultados") and len(callback["resultados"]) > 0:
        print(f"\n4️⃣  Verificando estructura de resultados...")
        resultado = callback["resultados"][0]

        result_checks = {
            "servicio_id": "servicio_id" in resultado,
            "propiedad_id": "propiedad_id" in resultado,
            "empresa": "empresa" in resultado,
            "tipo_servicio": "tipo_servicio" in resultado,
            "deuda": "deuda" in resultado,
            "exito": "exito" in resultado,
            "consulta_id": "consulta_id" in resultado,
        }

        for check, passed in result_checks.items():
            status = "✅" if passed else "❌"
            print(f"   {status} {check}: {resultado.get(check)}")
            if not passed:
                all_passed = False

    print(f"\n{'✅ TEST 1 PASÓ' if all_passed else '❌ TEST 1 FALLÓ'}")
    print("=" * 70)
    return all_passed


def test_callback_servicios_especificos():
    """Prueba el sistema de callbacks con servicios específicos"""
    print("\n" + "=" * 70)
    print("  TEST 2: Callback para servicios específicos")
    print("=" * 70)

    # Limpiar callbacks previos
    received_callbacks.clear()

    # Encolar consulta de servicios específicos
    print(f"\n1️⃣  Encolando consulta de servicios específicos...")
    response = requests.post(
        f"{BASE_URL}/consultar/servicios",
        json={
            "servicio_ids": [5, 6],  # Ajusta según tus datos
            "callback_url": CALLBACK_URL,
            "voucher_id": "test-voucher-456"
        }
    )

    if response.status_code != 200:
        print(f"❌ Error: {response.status_code} - {response.text}")
        return False

    job_data = response.json()
    job_id = job_data["job_id"]
    print(f"✅ Job encolado: {job_id}")
    print(f"   Total servicios: {job_data['total_servicios']}")

    # Esperar callback
    print(f"\n2️⃣  Esperando callback...")
    max_wait = 180
    start_time = time.time()

    while (time.time() - start_time) < max_wait:
        if len(received_callbacks) > 0:
            print(f"✅ Callback recibido después de {time.time() - start_time:.1f}s")
            break
        time.sleep(2)
        print(".", end="", flush=True)
    else:
        print(f"\n❌ No se recibió callback después de {max_wait}s")
        return False

    # Verificar
    callback = received_callbacks[0]
    voucher_ok = callback.get("voucher_id") == "test-voucher-456"
    resultados_ok = isinstance(callback.get("resultados"), list)

    print(f"\n3️⃣  Verificación:")
    print(f"   {'✅' if voucher_ok else '❌'} voucher_id correcto")
    print(f"   {'✅' if resultados_ok else '❌'} resultados es lista")
    print(f"   📊 Total resultados: {len(callback.get('resultados', []))}")

    passed = voucher_ok and resultados_ok
    print(f"\n{'✅ TEST 2 PASÓ' if passed else '❌ TEST 2 FALLÓ'}")
    print("=" * 70)
    return passed


def test_consulta_sin_callback():
    """Prueba que el sistema funciona sin callback (comportamiento original)"""
    print("\n" + "=" * 70)
    print("  TEST 3: Consulta sin callback (modo tradicional)")
    print("=" * 70)

    print(f"\n1️⃣  Encolando consulta sin callback...")
    response = requests.post(
        f"{BASE_URL}/consultar/propiedad",
        json={"propiedad_id": 35}
    )

    if response.status_code != 200:
        print(f"❌ Error: {response.status_code}")
        return False

    job_data = response.json()
    job_id = job_data["job_id"]
    print(f"✅ Job encolado: {job_id}")

    # Polling tradicional
    print(f"\n2️⃣  Haciendo polling del estado...")
    for i in range(30):
        response = requests.get(f"{BASE_URL}/job/{job_id}")
        job = response.json()

        if job["status"] == "completed":
            print(f"✅ Job completado después de {i * 2}s")
            print(f"   Resultados: {len(job.get('resultado', []))} servicios")
            print(f"\n✅ TEST 3 PASÓ")
            print("=" * 70)
            return True
        elif job["status"] == "failed":
            print(f"❌ Job falló: {job.get('error')}")
            return False

        time.sleep(2)
        print(".", end="", flush=True)

    print(f"\n❌ Timeout")
    print("=" * 70)
    return False


def main():
    """Ejecuta todas las pruebas"""
    print("\n" + "=" * 70)
    print("  PRUEBAS DEL SISTEMA DE CALLBACKS")
    print("=" * 70)
    print()

    # Iniciar servidor de callbacks en background
    print(f"🚀 Iniciando servidor de callbacks en puerto {CALLBACK_PORT}...")
    callback_thread = threading.Thread(target=start_callback_server, daemon=True)
    callback_thread.start()
    time.sleep(2)  # Esperar a que inicie

    try:
        # Verificar que la API principal esté corriendo
        print(f"🔍 Verificando API principal en {BASE_URL}...")
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code != 200:
            print(f"❌ API principal no está corriendo en {BASE_URL}")
            print(f"   Ejecuta: python api.py")
            return

        print(f"✅ API principal operativa")

        # Ejecutar pruebas
        results = []

        # TEST 1: Callback con propiedad
        results.append(("Callback propiedad", test_callback_propiedad()))
        time.sleep(3)

        # TEST 2: Callback con servicios específicos
        results.append(("Callback servicios", test_callback_servicios_especificos()))
        time.sleep(3)

        # TEST 3: Sin callback (modo tradicional)
        results.append(("Sin callback", test_consulta_sin_callback()))

        # Resumen
        print("\n" + "=" * 70)
        print("  RESUMEN DE PRUEBAS")
        print("=" * 70)

        passed = 0
        for name, result in results:
            status = "✅ PASÓ" if result else "❌ FALLÓ"
            print(f"  {status}: {name}")
            if result:
                passed += 1

        print()
        print(f"  Total: {passed}/{len(results)} pruebas pasaron")
        print("=" * 70)

        if passed == len(results):
            print("\n🎉 TODAS LAS PRUEBAS PASARON")
        else:
            print(f"\n⚠️  {len(results) - passed} prueba(s) fallaron")

    except requests.exceptions.ConnectionError:
        print(f"\n❌ ERROR: No se puede conectar a {BASE_URL}")
        print(f"   Asegúrate de que el servidor esté corriendo")
        print(f"   Ejecuta: python api.py")
    except Exception as e:
        print(f"\n❌ ERROR INESPERADO: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
