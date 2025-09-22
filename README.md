# Procesador de Actas Electorales

Este proyecto contiene un script en Python para procesar actas electorales de Bolivia obtenidas desde la OEP (Oficina Electoral Plurinacional).

## Descripción

El script realiza consultas asíncronas al endpoint de la OEP para obtener imágenes de actas electorales y las guarda localmente.

## Requisitos

- Python 3.7+
- Dependencias listadas en `pyproject.toml`
- [UV astral](https://docs.astral.sh/uv/)

## Instalación

```bash
uv sync
```

## Uso

1. Descargar los resultados de las elecciones en la página [https://computo.oep.org.bo/](https://computo.oep.org.bo/) en formato csv
2. Renombrar el archivo CSV a `resultados.csv`
3. Ejecutar el script:

```bash
uv run python procesar_actas.py
```

Las imágenes de las actas se guardarán en la carpeta `actas/` con el código de mesa como nombre de archivo.
