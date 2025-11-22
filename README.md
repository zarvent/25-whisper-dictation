# V2M ONYX EDITION

Voice-to-Machine transcription system con **Arquitectura Hexagonal** y **Ghost Core UI**.

## Características / FEATURES

- **JSON-RPC 2.0**: Protocolo robusto sobre Unix Socket.
- **Smart Batching (VAD)**: Detección inteligente de voz con Silero VAD.
- **Independence Switch**: Modo offline sin LLM.
- **Ghost Bar UI**: Interfaz minimalista en PySide6 + QML.
- **Auto-Reconnection**: SDK con retry automático.

## Instalación / INSTALLATION

```bash
# Instalar dependencias
pip install -r requirements.txt
```

## Uso / USAGE

### Opción 1: Scripts de inicio

```bash
# Terminal 1: Iniciar Daemon
./run_daemon.sh

# Terminal 2: Iniciar GUI
./run_gui.sh
```

### Opción 2: Manual

```bash
# Terminal 1: Daemon
PYTHONPATH=src python -m v2m.daemon

# Terminal 2: GUI
PYTHONPATH=src python -m v2m.gui.app
```

## Arquitectura / ARCHITECTURE

```
src/v2m/
├── core/           # RPC, CQRS, DI Container
├── application/    # Command Handlers, Services
├── infrastructure/ # Whisper, VAD, LLM, Audio
├── gui/            # PySide6 + QML UI
└── sdk.py          # Client SDK
```

## Controles GUI / GUI CONTROLS

- **Click en Ghost Bar**: Iniciar/Detener grabación.
- **Drag**: Mover ventana.

## Configuración / CONFIGURATION

Editar `config.toml` para ajustar:
- Modelo Whisper (`whisper_model`)
- VAD filters (`vad_filter`, `min_silence_duration_ms`)
- LLM API key (`GEMINI_API_KEY` o `GOOGLE_API_KEY`)

## Tests

```bash
# Test RPC Manual
PYTHONPATH=src python tests/test_rpc_manual.py

# Test SDK Reconnect
PYTHONPATH=src python tests/test_sdk_reconnect.py

# Test Bridge Integration
PYTHONPATH=src python tests/test_bridge_integration.py
```

---
**V2M ONYX EDITION** - Ghost Core Architecture by Zarvent
