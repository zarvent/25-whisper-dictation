# GUI (GRAPHICAL USER INTERFACE)

### qué es esta carpeta
contiene todo el código relacionado con la interfaz gráfica de usuario implementada en `pyside6` y `qml`

### para qué sirve
provee la "ghost bar" y otros elementos visuales con los que el usuario interactúa directamente se comunica con el `daemon` a través de `rpc` o `bridge` para ejecutar acciones

### qué puedo encontrar aquí
*   archivos `.qml` que definen la apariencia y comportamiento visual
*   controladores en python que conectan la lógica de la ui con el backend
*   `bridge.py` puente de comunicación entre qml y python

### uso y ejemplos
para ejecutar la gui se utiliza el script `run_gui.sh` o se invoca el módulo `v2m.gui.app`
