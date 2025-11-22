#!/bin/bash
# Script para iniciar el GUI de V2M Onyx

cd "$(dirname "$0")"

# Activar venv
source venv/bin/activate

# Exportar PYTHONPATH
export PYTHONPATH="$(pwd)/src"

# Iniciar GUI
python -m v2m.gui.app
