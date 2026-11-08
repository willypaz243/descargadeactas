# Guía para Obtener Credenciales de Firebase

## ❗ Importante

El archivo `credentials/service_account.json` es necesario para que el script pueda conectar a Firebase Storage. Si no lo tienes, sigue estos pasos.

## 📥 Cómo obtener el archivo de credenciales

### Paso 1: Acceder a Firebase Console
1. Ve a [Firebase Console](https://console.firebase.google.com/)
2. Selecciona tu proyecto: **rc-proyect-84398**

### Paso 2: Crear credenciales de servicio
1. En el menú lateral, haz clic en el ícono de **⚙️ (Project Settings)** 
2. En la sección "Your apps", haz clic en la pestaña **"Service accounts"**
3. Haz clic en el botón **"Generate new private key"**
4. Acepta el aviso de seguridad
5. Se descargará un archivo JSON

### Paso 3: Colocar el archivo
1. Crea la carpeta `credentials/` en la raíz del proyecto y mueve ahí el JSON descargado:
   ```
   credentials/
   ```
2. Renómbralo como: `credentials/service_account.json`

> La carpeta `credentials/` está en `.gitignore`, así que las llaves nunca llegan al repositorio.

## 📝 Plantilla

Existe una plantilla sin valores reales en `credentials/service_account.example.json`. Puedes copiarla y reemplazar los campos:

```bash
cp credentials/service_account.example.json credentials/service_account.json
```

## ⚠️ Seguridad

- **Este archivo contiene credenciales que permiten acceder a tu proyecto Firebase.**
- **Nunca compartir este archivo públicamente.**
- **No subirlo a repositorios Git públicos.**
- **Si está comprometido, regenera las credenciales en Firebase Console.**

## 🚫 Si no quieres usar credenciales

Si no tienes el archivo de credenciales, el script funcionará en **modo demostración**:
```bash
uv run python upload_to_firebase.py
```

El script mostrará "Subida en modo demostración" y no subirá los archivos realmente, pero podrás ver los mensajes de progreso.

## ✅ Verificar conexión

Una vez que tengas el archivo `credentials/service_account.json`, el script debería mostrar:

```
✓ Conexión a Firebase Storage establecida
  Archivo de configuración: /ruta/a/credentials/service_account.json
```

Si ves este mensaje, ¡estás listo para subir tus archivos!

## 🆘 Si sigues teniendo problemas

1. Verifica que el archivo JSON sea válido (puedes usar un validador JSON en línea)
2. Asegúrate de que el archivo se llame `credentials/service_account.json`
3. Verifica que esté en la misma carpeta que el script
4. Revisa los permisos del archivo (`chmod 600 credentials/service_account.json`)
