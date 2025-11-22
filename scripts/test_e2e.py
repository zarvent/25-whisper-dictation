#!/usr/bin/env python3
"""
script de prueba end-to-end para verificar que v2m funciona correctamente
"""
import asyncio
import sys
from pathlib import Path

# agregar src al pythonpath
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from v2m.sdk import V2MClient


async def test_connection():
    """verifica que el daemon esté corriendo"""
    print("🔍 probando conexión al daemon...")
    client = V2MClient()

    try:
        connected = await client.connect()
        if connected:
            print("✅ daemon conectado correctamente")
            return True
        else:
            print("❌ daemon no responde")
            return False
    except Exception as e:
        print(f"❌ error conectando al daemon: {e}")
        return False


async def test_status():
    """verifica el estado del daemon"""
    print("\n🔍 obteniendo estado del daemon...")
    client = V2MClient()

    try:
        status = await client.get_status()
        print(f"✅ estado: {status}")
        return True
    except Exception as e:
        print(f"❌ error obteniendo estado: {e}")
        return False


async def test_transcribe_simulation():
    """simula una transcripción (requiere hablar al micrófono)"""
    print("\n🔍 probando transcripción...")
    print("⚠️  NOTA: este test requiere que hables al micrófono")
    print("    el daemon grabará hasta detectar silencio (VAD)")

    response = input("\n¿quieres continuar con el test de transcripción? (s/n): ")
    if response.lower() != 's':
        print("⏭️  saltando test de transcripción")
        return True

    client = V2MClient()

    try:
        print("\n🎤 habla ahora... (el daemon detectará silencio automáticamente)")
        result = await client.transcribe(use_llm=True)

        text = result.get('text', '')
        original = result.get('original', '')

        print(f"\n✅ transcripción completada:")
        if original and original != text:
            print(f"   📝 original (whisper): {original}")
            print(f"   ✨ refinado (gemini): {text}")
        else:
            print(f"   📝 texto: {text}")

        return True
    except Exception as e:
        print(f"❌ error en transcripción: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """ejecuta todos los tests"""
    print("=" * 60)
    print("V2M END-TO-END TEST SUITE")
    print("=" * 60)

    tests = [
        ("conexión", test_connection),
        ("estado", test_status),
        ("transcripción", test_transcribe_simulation),
    ]

    results = []
    for name, test_func in tests:
        try:
            result = await test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ test '{name}' falló con excepción: {e}")
            results.append((name, False))

    print("\n" + "=" * 60)
    print("RESUMEN DE TESTS")
    print("=" * 60)

    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")

    all_passed = all(r for _, r in results)
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 TODOS LOS TESTS PASARON")
    else:
        print("⚠️  ALGUNOS TESTS FALLARON")
    print("=" * 60)

    return 0 if all_passed else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
