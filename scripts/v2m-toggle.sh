#!/bin/bash

# Script actualizado para usar el nuevo SDK JSON-RPC

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" > /dev/null 2>&1 && pwd )"
PROJECT_DIR="$( dirname "${SCRIPT_DIR}" )"

VENV_PATH="${PROJECT_DIR}/venv"
PYTHON="${VENV_PATH}/bin/python"

# Activar venv y exportar PYTHONPATH
if [ ! -f "${VENV_PATH}/bin/activate" ]; then
    notify-send "❌ Error de V2M" "Entorno virtual no encontrado"
    exit 1
fi

source "${VENV_PATH}/bin/activate"
export PYTHONPATH="${PROJECT_DIR}/src"

# Usar el nuevo SDK para smart_capture
${PYTHON} -c "
import asyncio
from v2m.sdk import V2MClient
import sys

async def smart_capture():
    try:
        client = V2MClient()
        await client.connect()
        result = await client.transcribe(use_llm=False)
        text = result.get('text', '')
        print(f\"Transcription: {text}\")
    except Exception as e:
        print(f\"Error: {e}\", file=sys.stderr)
        sys.exit(1)

asyncio.run(smart_capture())
" 2>&1 | tee /tmp/v2m_toggle.log

# Capturar el exit code del script python
EXIT_CODE=${PIPESTATUS[0]}

if [ $EXIT_CODE -ne 0 ]; then
    notify-send "❌ V2M Error" "Ver /tmp/v2m_toggle.log"
    exit $EXIT_CODE
fi
