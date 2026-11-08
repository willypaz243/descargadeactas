# Instrucciones para Subir Actas a Firebase Storage

## ⚠️ REQUISITO OBLIGATORIO

El script **REQUIERE** un archivo de credenciales JSON (`credentials/service_account.json`) para conectar a Firebase Storage.

Si no tienes este archivo, sigue la guía en [Guía de credenciales](FIREBASE_CREDENTIALS_GUIDE.md)

## 📋 Requisitos Previos

1. **Instalar dependencias Python:**
   ```bash
   cd /home/willypaz/Workspace/working/devsCBBA/acta_audits/acta_donwloads
   pip install -e .
   ```

2. **Tener el archivo `credentials/service_account.json`:**
   - Descárgalo desde Firebase Console
   - Guía: [Guía de credenciales](FIREBASE_CREDENTIALS_GUIDE.md)

## 📂 Estructura de Archivos

El script espera la siguiente estructura de carpetas:

```
acta_donwloads/
├── actas/
│   ├── departamentales/
│   │   ├── {nro_acta}.jpg
│   │   └── ...
│   └── municipales/
│       ├── {nro_acta}.jpg
│       └── ...
├── credentials/
│   └── service_account.json  ✅ REQUERIDO (ignorado por git)
├── docs/
├── scripts/
├── upload_to_firebase.py
└── pyproject.toml
```

## 🚀 Uso

### Ejecutar el script
```bash
uv run python upload_to_firebase.py
```

### Verificar conexión

Si tienes el archivo de credenciales, el script debe mostrar:
```
✓ Conexión a Firebase Storage establecida
  Archivo de configuración: /ruta/a/credentials/service_account.json
```

Si ves este mensaje, ¡estás listo para subir!

## 📤 Estructura de Firebase Storage

Los archivos se subirán siguiendo esta estructura:

### Para Departamentales
```
mesas/
└── departamentales/
    ├── {nro_acta}.jpg
    ├── {nro_acta}.jpg
    └── ...
```

### Para Municipales
```
mesas/
└── {nro_acta}/
    ├── {nro_acta}.jpg
    ├── {nro_acta}.jpg
    └── ...
```

**Ejemplos:**
- `actas/departamentales/1234567.jpg` → `mesas/departamentales/1234567.jpg`
- `actas/municipales/201570.jpg` → `mesas/201570/201570.jpg`
- `actas/municipales/3.jpg` → `mesas/000003/000003.jpg`

## 🔧 Personalización

### Modificar el script

Si necesitas cambiar la estructura, edita el archivo `upload_to_firebase.py`:

1. **Ruta de las credenciales:**
   ```python
   firebase_config = '/ruta/a/tu/archivo.json'
   ```

2. **Rutas de los directorios:**
   ```python
   directories = [
       ('actas/departamentales', 'departamental'),
       ('actas/municipales', 'municipal')
   ]
   ```

3. **Formato de las rutas:**
   ```python
   if target_type == 'departamental':
       blob_path = f"mesas/departamentales/{filename}.jpg"
   else:  # municipal
       blob_path = f"mesas/{filename}/{filename}.jpg"
   ```

### Agregar más directorios

Puedes agregar más directorios simplemente agregando más líneas a la lista:

```python
directories = [
    ('actas/departamentales', 'departamental'),
    ('actas/municipales', 'municipal'),
    ('actas/otro', 'otro_tipo')
]
```

## 📊 Salida del Script

El script mostrará un resumen al final:

```
============================================================
INICIO DE PROCESO DE SUBIDA
============================================================

============================================================
Procesando directorio: actas/departamentales
Tipo: departamental
============================================================

Encontrados 5 archivos .jpg

Procesando: 1234567
✓ Subido exitosamente: mesas/departamentales/1234567.jpg
  URL pública: https://firebasestorage.app/...

Procesando: 201570
✓ Subido exitosamente: mesas/departamentales/201570.jpg
  URL pública: https://firebasestorage.app/...

============================================================
RESUMEN
============================================================
Total de archivos: 5
Éxitosos: 5
Fallidos: 0
Tiempo: 15.32 segundos
============================================================
```

## ⚠️ Notas Importantes

1. **OBLIGATORIO:** El archivo `credentials/service_account.json` es necesario para la subida real
2. **Formato de archivos:** Los archivos .jpg se suben como .jpg (no se convierten a .webp)
3. **Nombres de archivo:** Usa el número de acta como nombre de archivo (ej: `1234567.jpg`)
4. **Formato de ID:** El número de acta se formatea a 6 dígitos con ceros a la izquierda (ej: `1234` → `001234`)
5. **Tiempo de espera:** El script incluye pausas entre subidas para no saturar la API
6. **Modo demostración:** Si no tienes las credenciales, el script se ejecutará pero no subirá nada realmente

## 🔒 Seguridad

- **⚠️ El archivo de credenciales `credentials/service_account.json` debe mantenerse confidencial**
- **Nunca compartir este archivo públicamente**
- **No subirlo a repositorios Git públicos**
- **Si está comprometido, regenera las credenciales en Firebase Console**

## 📝 Referencias

- [Firebase Admin SDK Documentation](https://firebase.google.com/docs/admin/setup)
- [Firebase Storage Python SDK](https://firebase.google.com/docs/storage/admin/start)
- [Guía de Credenciales](FIREBASE_CREDENTIALS_GUIDE.md)
