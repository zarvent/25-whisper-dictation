# CQRS (COMMAND QUERY RESPONSIBILITY SEGREGATION)

### qué es esta carpeta
implementa los componentes necesarios para el patrón `CQRS` separando las operaciones de lectura (queries) de las de escritura (commands)

### para qué sirve
permite escalar y mantener lógica compleja separando la intención de modificar el estado del sistema (commands) de la consulta de datos (queries) esto facilita un diseño más limpio y desacoplado

### qué puedo encontrar aquí
*   `bus.py` implementación del bus de comandos que enruta mensajes a sus handlers
*   `interfaces.py` definiciones base para comandos y handlers

### uso y ejemplos
```python
# comando
class MyCommand:
    pass

# handler
class MyHandler:
    def handle(self, command: MyCommand):
        pass
```
