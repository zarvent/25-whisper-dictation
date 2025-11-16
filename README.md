🗣️ **herramienta de dictado por voz (refactorizada)**

---

🎯 **propósito**

el propósito es simple: poder dictar texto en cualquier lugar del sistema operativo.

la idea es que puedas transcribir audio por GPU (para máxima velocidad) en cualquier campo de texto, sin importar la aplicación.

este proyecto es una refactorización de un script simple que tenía. lo moví a una aplicación modular de Python para separar las responsabilidades (transcripción vs. lógica de LLM) y hacerlo mucho más fácil de mantener y configurar a futuro.

---

🕹️ **interacción y flujo de trabajo**

la interacción se divide en dos funciones principales. ambas están pensadas para ser activadas con atajos de teclado globales, para que no interrumpan tu flujo de trabajo.

**1. flujo de dictado (voz → texto)**

este es el flujo principal: capturar tu voz y convertirla en texto. está activado por `scripts/whisper-toggle.sh`.

```mermaid
flowchart TD
    A[⏺️ atajo (ej. ctrl+mayús+espacio)] --> B(inicia grabación 🎤);
    B --> C[⏹️ atajo (mismo)];
    C --> D{transcribe con Whisper};
    D --> E[📋 copiado al portapapeles];
```

**2. flujo de refinado (texto → texto mejorado)**

a veces la transcripción no es perfecta. este flujo toma el texto de tu portapapeles y usa un LLM para limpiarlo, corregirlo o formatearlo. está activado por `scripts/process-clipboard.sh`.

```mermaid
flowchart TD
    A[📋 copias texto] --> B(🧠 atajo secundario);
    B --> C{procesa con LLM (Gemini)};
    C --> D[📋 reemplaza portapapeles];
```

---

🧩 **el núcleo: de scripts a aplicación**

aquí está el cambio principal de la refactorización. esto ya no es un simple script; es una aplicación de Python que sigue principios de diseño más robustos. decidí usar inyección de dependencias (DI) y un bus de comandos (un CQRS liviano) para orquestar los diferentes servicios. esto hace que el sistema sea mucho más desacoplado y fácil de probar o extender.

**archivos y directorios clave:**

*   `src/whisper_dictation/main.py`: es el 'controlador' principal. escucha los comandos (`start`, `stop`, `process`) desde los scripts de shell.
*   `src/whisper_dictation/core/di/container.py`: aquí es donde se 'cablea' todo. define qué implementación concreta se usa para cada interfaz (ej. 'usar Gemini para el servicio LLM').
*   `src/whisper_dictation/application/`: el 'cerebro' de la app. contiene la lógica de negocio pura (los comandos y los handlers que saben qué hacer con ellos).
*   `src/whisper_dictation/infrastructure/`: las 'manos' de la app. aquí viven las implementaciones que hablan con el mundo real:
    *   `whisper_transcription_service.py`: se encarga de cargar `faster-whisper` y hacer la grabación/transcripción.
    *   `gemini_llm_service.py`: maneja la conexión con la API de Google Gemini para el refinado.
*   `config.toml`: tu panel de control. aquí defines qué modelo de Whisper usar, si correr en `cuda` o `cpu`, y otros parámetros.
*   `.env`: solo para tus secretos. aquí va tu `GEMINI_API_KEY`.

---

🛠️ **instalación y diagnóstico**

para poner esto en marcha, necesitas configurar tres capas: el sistema, Python y la IA.

**1. dependencias del sistema:**

primero, lo básico del sistema. `ffmpeg` y `pactl` son para grabar, y `xclip` para copiar al portapapeles. si tienes una GPU NVIDIA, asegúrate de que CUDA esté listo.

*   asegúrate de tener `ffmpeg`, `xclip` y `pactl`.
*   (opcional pero recomendado) drivers de NVIDIA y CUDA toolkit si usas `device: "cuda"`.

**2. entorno de Python:**

es una buena práctica usar un entorno virtual. esto mantiene las dependencias del proyecto aisladas.

```bash
# crear un entorno virtual
python3 -m venv venv

# activar el entorno
source venv/bin/activate

# instalar dependencias
pip install -r requirements.txt
```

**3. configuración de IA (Gemini):**

para el refinado de texto, la app necesita tu clave de API de Gemini. la leemos desde un archivo `.env` para no 'quemarla' en el código.

```bash
# crear el archivo .env si no existe
touch .env

# añadir tu api key de gemini al archivo .env
echo 'GEMINI_API_KEY="AIzaSy..."' > .env
```

**4. configuración de la aplicación:**

echa un vistazo a `config.toml`. aquí es donde puedes afinar el rendimiento, como elegir un modelo de Whisper más pequeño si `large-v2` es demasiado pesado.

*   revisa `config.toml`.
*   asegúrate que `[whisper]` apunte al modelo y dispositivo correctos (ej. `model = "large-v2"`, `device = "cuda"`).

**5. verificación:**

para asegurar que todo esté conectado:

*   `scripts/verify-setup.sh` te da un chequeo rápido de las dependencias.
*   `python test_whisper_gpu.py` es útil para confirmar que `faster-whisper` está usando tu GPU (y no el CPU).

---

📚 **archivos históricos**

si te interesa el 'cómo' y 'por qué' de la evolución de este proyecto, dejé algunas notas en el archivo:

*   `archives/2025-11-16 MIGRATION.md` (detalles sobre la migración de perplexity a Gemini).
*   `archives/2025-11-15 nueva feature.md` (justificación de la feature de refinado).
*   `prompts/refine_system.txt` (el prompt exacto que usa Gemini).

---
*nota sobre la visualización en vs code: si los diagramas de flujo no se muestran, asegúrate de tener instalada una extensión compatible con mermaid, como "markdown mermaid".*
