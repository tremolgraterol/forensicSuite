# Guía de contribución

¡Gracias por interesarte en contribuir a ForensicSuite! Este proyecto es de carácter educativo y todo aporte que mejore la calidad, seguridad o claridad del código es bienvenido.

## Cómo contribuir

1. Haz un **fork** del repositorio.
2. Crea una rama para tu cambio:
   ```bash
   git checkout -b feature/nombre-descriptivo
   ```
3. Realiza tus cambios siguiendo las convenciones del proyecto.
4. Ejecuta los tests localmente:
   ```bash
   python -m pytest
   ```
5. Asegúrate de que tu código no introduce advertencias de seguridad obvias.
6. Escribe un mensaje de commit claro y descriptivo.
7. Abre un **Pull Request** explicando el problema que resuelves o la mejora que introduces.

## Convenciones de código

- Python 3.9 o superior.
- Usa nombres descriptivos en español o inglés técnico, según el contexto.
- Documenta funciones públicas y clases con docstrings.
- Mantén la compatibilidad con Linux y, cuando aplique, con Windows.
- No incluyas claves, contraseñas ni información personal en el código.

## Reportar errores

Si encuentras un bug, abre un **Issue** usando la plantilla correspondiente e incluye:

- Versión de ForensicSuite.
- Sistema operativo y versión de Python.
- Pasos para reproducir el error.
- Mensaje de error completo.
- Comportamiento esperado.

## Proponer mejoras

Usa la categoría **Ideas** en GitHub Discussions o abre un Issue con la plantilla de *feature request*.

## Áreas de especial interés

- Mejoras en seguridad y validación de entradas.
- Nuevos perfiles de carving.
- Integraciones con Volatility3.
- Mejoras en documentación y traducciones.
- Tests unitarios y de integración.

## Código de conducta

Al participar en este proyecto aceptas seguir nuestro [Código de Conducta](CODE_OF_CONDUCT.md).
