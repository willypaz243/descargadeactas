# Descargador y subidor de actas electorales (OEP Bolivia)

Scripts en Python que descargan las imágenes de los actas de los resultados electorales
desde la [OEP](https://computo.oep.org.bo/) y las suben a Firebase Storage.

## Estructura

```
.
├── procesar_actas.py              # Descarga actas nacionales → actas/
├── process_actas_subnationals.py  # Descarga actas subnacionales (gobernadores/alcaldes)
├── upload_to_firebase.py          # Sube actas/ a Firebase Storage
├── scripts/                       # Pruebas de conexión / subida a Firebase
│   ├── test_firebase_connection.py
│   └── test_firebase_connection_separated.py
├── credentials/                   # Llaves de servicio (ignorado por git)
│   └── service_account.example.json
├── docs/                          # Guías del pipeline de subida
└── actas/                         # Imágenes descargadas (ignorado por git)
```

## Requisitos

- Python 3.12+
- [UV astral](https://docs.astral.sh/uv/)

```bash
uv sync
```

## 1. Descargar actas

1. Descarga los resultados de las elecciones desde [computo.oep.org.bo](https://computo.oep.org.bo/) en CSV.
2. Renombra el archivo a `resultados.csv` (este archivo y las imágenes descargadas están ignorados por git).
3. Ejecuta:

```bash
uv run python procesar_actas.py            # actas nacionales
uv run python process_actas_subnationals.py  # actas subnacionales
```

Las imágenes se guardan en `actas/` (o `subnational_actas_2da_vuelta/`) con el código de mesa como nombre.

## 2. Subir a Firebase Storage

Coloca la llave de servicio en `credentials/service_account.json` (la carpeta está en `.gitignore`,
nunca se sube al repositorio). Guía paso a paso: [docs/FIREBASE_CREDENTIALS_GUIDE.md](docs/FIREBASE_CREDENTIALS_GUIDE.md).

```bash
uv run python scripts/test_firebase_connection.py  # verifica conexión y permisos
uv run python upload_to_firebase.py                # subida masiva
```

Detalles de rutas usadas en el bucket: [docs/UPLOAD_INSTRUCTIONS.md](docs/UPLOAD_INSTRUCTIONS.md).

## Seguridad

- Las credenciales viven solo en `credentials/` y están ignoradas por git.
- Si una llave se filtra, regenérela en Firebase Console.
