# INFRASTRUCTURE AUDIO

### qué es esta carpeta
contiene las implementaciones concretas para la captura y procesamiento de audio a bajo nivel

### para qué sirve
abstrae la complejidad del hardware de audio (micrófonos drivers) proveyendo una interfaz limpia para que el resto de la aplicación pueda consumir audio sin preocuparse por los detalles técnicos

### qué puedo encontrar aquí
*   implementaciones de `AudioSource` usando librerías como `sounddevice` o `pyaudio`
*   manejo de buffers de audio (eg `ring buffers`) para grabación eficiente

### uso y ejemplos
esta capa es utilizada por los servicios de aplicación para obtener streams de datos de audio crudos
