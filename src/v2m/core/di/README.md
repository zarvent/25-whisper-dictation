# DEPENDENCY INJECTION

### qué es esta carpeta
contiene la lógica relacionada con el patrón de inyección de dependencias es el mecanismo central para gestionar cómo se crean y conectan los objetos en la aplicación

### para qué sirve
permite desacoplar las clases de sus dependencias directas facilitando el testing y la mantenibilidad en lugar de que una clase cree sus propias dependencias (usando `new` o constructores directos) estas se le "inyectan" desde fuera usualmente gestionadas por un contenedor

### qué puedo encontrar aquí
*   `container.py` la implementación del contenedor de dependencias que registra y resuelve los objetos
*   `providers.py` (opcional) definiciones de cómo instanciar objetos complejos

### uso y ejemplos
```python
# registro
container.register(ServiceClass, ServiceImplementation())

# resolución
service = container.resolve(ServiceClass)
```
