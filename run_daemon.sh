#!/bin/bash
# Script para iniciar el Daemon de V2M

cd "$(dirname "$0")"

# Activar venv
source venv/bin/activate

# Exportar PYTHONPATH
export PYTHONPATH="$(pwd)/src"

# Iniciar Daemon
python -m v2m.daemon
