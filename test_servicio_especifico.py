"""
Test para un servicio específico
"""
import asyncio
from batch_processor import BatchProcessor


async def test_servicio(servicio_id: int):
    """Prueba consultar un servicio específico"""
    print(f"\n{'='*60}")
    print(f"   TEST DE SERVICIO ID: {servicio_id}")
    print(f"{'='*60}\n")

    try:
        processor = BatchProcessor()

        # Consultar solo este servicio
        resultados = await processor.procesar_servicios_especificos([servicio_id])
        await processor.close()

        if resultados:
            resultado = resultados[0]
            print(f"\n{'='*60}")
            print(f"   RESULTADO")
            print(f"{'='*60}")
            print(f"Servicio ID: {resultado['servicio_id']}")
            print(f"Empresa: {resultado['empresa']}")
            print(f"Éxito: {'✅' if resultado['exito'] else '❌'}")
            print(f"Deuda: ${resultado.get('deuda', 0)}")
            if resultado.get('error'):
                print(f"Error: {resultado['error']}")
            print(f"{'='*60}\n")
        else:
            print("❌ No se obtuvieron resultados")

    except Exception as e:
        print(f"❌ Error en el test: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    import sys
    servicio_id = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    asyncio.run(test_servicio(servicio_id))
