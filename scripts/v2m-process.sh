#!/bin/bash

# Script para procesar texto del clipboard con Gemini
# Este script SOLO hace refinamiento LLM (separation of concerns)

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" > /dev/null 2>&1 && pwd )"
PROJECT_DIR="$( dirname "${SCRIPT_DIR}" )"

VENV_PATH="${PROJECT_DIR}/venv"
PYTHON="${VENV_PATH}/bin/python"

# Validación
if [ ! -f "${VENV_PATH}/bin/activate" ]; then
    notify-send "❌ Error de V2M" "Entorno virtual no encontrado"
    exit 1
fi

source "${VENV_PATH}/bin/activate"
export PYTHONPATH="${PROJECT_DIR}/src"

# Procesamiento directo con SDK
${PYTHON} -c "
import asyncio
import sys
from v2m.sdk import V2MClient
from v2m.infrastructure.linux_adapters import LinuxClipboardAdapter

async def process_clipboard():
    try:
        # 1. Obtener texto del clipboard
        clipboard = LinuxClipboardAdapter()
        text = clipboard.paste()

        if not text or not text.strip():
            print('Clipboard vacío.')
            sys.exit(1)

        print(f'Procesando {len(text)} caracteres...')

        # 2. Conectar y procesar
        client = V2MClient()
        await client.connect()

        # 3. Llamar al nuevo método RPC process_text
        result = await client._send_request('process_text', {'text': text})

        refined_text = result.get('text', '')
        print(f'✅ Procesamiento completado: {len(refined_text)} caracteres')

    except Exception as e:
        print(f'Error: {e}', file=sys.stderr)
        sys.exit(1)

asyncio.run(process_clipboard())
" 2>&1 | tee /tmp/v2m_process.log

# Capturar exit code
EXIT_CODE=${PIPESTATUS[0]}

if [ $EXIT_CODE -ne 0 ]; then
    notify-send "❌ V2M Process Error" "Ver /tmp/v2m_process.log"
    exit $EXIT_CODE
fi
