"""
Script de prueba para verificar el sistema completo
"""
import asyncio
from database import db
from prompt_generator import PromptGenerator
from batch_processor import BatchProcessor


async def test_conexion_db():
    """Prueba la conexión a Supabase"""
    print("=== TEST 1: Conexión a Supabase ===")
    try:
        # Probar obtener empresas
        empresa = db.get_empresa_servicio("Metrogas")
        if empresa:
            print(f"✅ Conexión exitosa a Supabase")
            print(f"   Empresa encontrada: {empresa['nombre']}")
            print(f"   URL: {empresa['url_servipag']}")
        else:
            print("❌ No se encontró la empresa Metrogas")
    except Exception as e:
        print(f"❌ Error de conexión: {str(e)}")
    print()


async def test_prompt_generator():
    """Prueba el generador de prompts"""
    print("=== TEST 2: Generador de Prompts ===")
    try:
        empresa = db.get_empresa_servicio("Metrogas")
        servicio_mock = {
            "servicio_id": 999,
            "propiedad_id": 35,
            "compania": "Metrogas",
            "credenciales": {"identificador": "900728824"}
        }

        prompt = PromptGenerator.generate_prompt_from_servicio(servicio_mock, empresa)
        print("✅ Prompt generado exitosamente")
        print(f"   Longitud: {len(prompt)} caracteres")
        print(f"   Preview: {prompt[:150]}...")
    except Exception as e:
        print(f"❌ Error generando prompt: {str(e)}")
    print()


async def test_consultar_servicio():
    """Prueba consultar un servicio real"""
    print("=== TEST 3: Consulta de Servicio Real ===")
    try:
        # Obtener un servicio real de la BD
        servicios = db.get_todas_propiedades_con_servicios()
        if not servicios:
            print("⚠️  No hay servicios registrados en la base de datos")
            return

        servicio = servicios[0]
        print(f"Consultando: {servicio['compania']} (propiedad {servicio['propiedad_id']})")

        processor = BatchProcessor()
        resultado = await processor.procesar_servicio(servicio)
        await processor.close()

        if resultado['exito']:
            print(f"✅ Consulta exitosa")
            print(f"   Deuda: ${resultado['deuda']}")
        else:
            print(f"❌ Error en consulta: {resultado['error']}")

    except Exception as e:
        print(f"❌ Error en test: {str(e)}")
    print()


async def test_historial():
    """Prueba obtener historial de consultas"""
    print("=== TEST 4: Historial de Consultas ===")
    try:
        # Obtener historial de la primera propiedad con servicios
        servicios = db.get_todas_propiedades_con_servicios()
        if servicios:
            propiedad_id = servicios[0]['propiedad_id']
            historial = db.get_ultimas_consultas_propiedad(propiedad_id, limit=5)
            print(f"✅ Historial obtenido")
            print(f"   Propiedad ID: {propiedad_id}")
            print(f"   Registros encontrados: {len(historial)}")
            if historial:
                print(f"   Última consulta: {historial[0]['fecha_consulta']}")
        else:
            print("⚠️  No hay servicios para probar historial")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    print()


async def main():
    """Ejecuta todos los tests"""
    print("\n" + "="*60)
    print("   PRUEBAS DEL SISTEMA DE CONSULTA DE DEUDAS")
    print("="*60 + "\n")

    await test_conexion_db()
    await test_prompt_generator()

    # Preguntar si quiere hacer consulta real (consume API de browser-use)
    print("⚠️  El siguiente test hará una consulta real con browser-use")
    print("   Esto consumirá créditos de tu API key")
    respuesta = input("   ¿Continuar? (s/n): ")

    if respuesta.lower() == 's':
        await test_consultar_servicio()
        await test_historial()
    else:
        print("   Tests de consulta real omitidos\n")

    print("="*60)
    print("   TESTS COMPLETADOS")
    print("="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
