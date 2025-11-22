# V2M ONYX EDITION

voice-to-machine transcription system con **arquitectura hexagonal** y **ghost core ui**

## características

*   **JSON-RPC 2.0** protocolo robusto sobre unix socket
*   **smart batching (VAD)** detección inteligente de voz con silero vad
*   **independence switch** modo offline sin LLM
*   **ghost bar ui** interfaz minimalista en pyside6 + qml
*   **auto-reconnection** sdk con retry automático

## instalación

```bash
# instalar dependencias
pip install -r requirements.txt
```

## uso

### opción 1 scripts de inicio

```bash
# terminal 1 iniciar daemon
./run_daemon.sh

# terminal 2 iniciar gui
./run_gui.sh
```

### opción 2 manual

```bash
# terminal 1 daemon
PYTHONPATH=src python -m v2m.daemon

# terminal 2 gui
PYTHONPATH=src python -m v2m.gui.app
```

## arquitectura

```
src/v2m/
├── core/           # RPC, CQRS, DI container
├── application/    # command handlers, services
├── infrastructure/ # whisper, vad, LLM, audio
├── gui/            # pyside6 + qml ui
└── sdk.py          # client sdk
```

## controles gui

*   **click en ghost bar** iniciar o detener grabación
*   **drag** mover ventana

## configuración

editar `config.toml` para ajustar

*   modelo whisper `whisper_model`
*   vad filters `vad_filter` `min_silence_duration_ms`
*   LLM API key `GEMINI_API_KEY` o `GOOGLE_API_KEY`

## tests

```bash
# test RPC manual
PYTHONPATH=src python tests/test_rpc_manual.py

# test sdk reconnect
PYTHONPATH=src python tests/test_sdk_reconnect.py

# test bridge integration
PYTHONPATH=src python tests/test_bridge_integration.py
```

---
**V2M ONYX EDITION** ghost core architecture por zarvent
