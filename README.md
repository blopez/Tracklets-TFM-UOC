# Detección de peligros usando Tracklets y reidentificación de objetos

**Autor: Borja López Gómez**

## Instalación y ejecución
Los ficheros de código fuente han sido desarrollados contra la versión 0.9.15 de CARLA, usando Python 3.8 (la versión 3.9 ha dado problemas a la hora de instalar dependencias).

En primer lugar es necesario ejecutar las dependencias necesarias, mediante el comando ```pip install -r requirements.txt```.

Una vez tenemos todas las dependencias instaladas (puede ser entorno físico o virtual), ya podemos ejecutar cualquiera de los 2 procesos disponibles:

Proceso 1 (con CARLA abierto): preparación de entorno en intersección, y generación masiva de imágenes en disco:
```python .\one_intersection_controlled_v2.py```

Proceso 2: post procesado de las imágenes en disco para identificar peligros en tracklets (con detección de objetos, extracción de características y unidad central de procesamiento):
```python .\hazard_identification.py```

## Licencia
Este proyecto está licenciado bajo licencia MIT [(LICENSE.md)](LICENSE.md)


