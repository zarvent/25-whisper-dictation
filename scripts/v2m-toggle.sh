#!/bin/bash

# Script actualizado para usar el nuevo SDK JSON-RPC

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
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

async def smart_capture():
    client = V2MClient()
    await client.connect()
    result = await client.transcribe(use_llm=True)
    print(f\"Transcription: {result.get('text', '')}\")

asyncio.run(smart_capture())
"
