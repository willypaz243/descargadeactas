#!/usr/bin/env python3
"""
Script de prueba para subir un solo archivo a Firebase Storage
Captura mensajes de error detallados para pedir permisos al administrador
"""

import os
import sys
import traceback

from firebase_admin import credentials, initialize_app, storage
from google.api_core import exceptions

public_url = None


def test_firebase_connection():
    """Probar conexión a Firebase Storage"""
    print("=" * 60)
    print("PRUEBA DE CONEXIÓN A FIREBASE STORAGE")
    print("=" * 60)

    try:
        # Inicializar Firebase
        print("\n1. Inicializando Firebase...")
        cred = credentials.Certificate("credentials/service_account.json")
        initialize_app(cred, {"storageBucket": "rc-proyect-84398.firebasestorage.app"})
        print("   ✓ Conexión exitosa")

        # Obtener bucket
        print("\n2. Obteniendo bucket de Storage...")
        bucket = storage.bucket("rc-proyect-84398.firebasestorage.app")
        print(f"   ✓ Bucket obtenido: {bucket.name}")

        return True

    except Exception:
        print("\n✗ Error de conexión:")
        traceback.print_exc()
        return False


def test_file_upload():
    """Probar subir el archivo de prueba"""
    print("\n" + "=" * 60)
    print("PRUEBA DE SUBIDA DE ARCHIVO ESPECÍFICO")
    print("=" * 60)

    # Archivo específico
    local_file = "actas/departamentales/2083311.jpg"
    blob_path = "mesas/gobernatura/2083311.jpg"

    print(f"\n1. Archivo local: {local_file}")
    print(f"   Bucket destino: {blob_path}")

    try:
        print("\n2. Verificando archivo local...")
        if not os.path.exists(local_file):
            print(f"   ✗ El archivo no existe: {local_file}")
            return False, None
        print("   ✓ Archivo existe")

        print("\n3. Obteniendo bucket...")
        bucket = storage.bucket("rc-proyect-84398.firebasestorage.app")

        print("\n4. Creando blob...")
        blob = bucket.blob(blob_path)
        print(f"   ✓ Blob creado: {blob.name}")

        print("\n5. Subiendo archivo...")
        blob.upload_from_filename(local_file)
        print("   ✓ Archivo subido exitosamente")

        print("\n6. Haciendo el archivo público...")
        blob.make_public()
        print(f"   ✓ URL pública: {blob.public_url}")

        return True, blob

    except exceptions.Forbidden as e:
        print(
            f"ERROR DE PERMISOS: La cuenta de servicio no tiene acceso al bucket. {e}"
        )
    except exceptions.NotFound as e:
        print(f"ERROR DE RUTA: El bucket o el archivo no existen. {e}")
    except Exception as e:
        # Esto imprimirá el JSON de error completo que devuelve Google
        print("--- DETALLE DEL ERROR ---")
        print(f"Tipo: {type(e).__name__}")
        print(f"Mensaje: {e}")

    return False, None


def main():
    print("\n" + "=" * 60)
    print("SCRIPT DE PRUEBA FIREBASE STORAGE")
    print("=" * 60)

    # Probar conexión
    if not test_firebase_connection():
        print("\n❌ No se puede conectar a Firebase Storage.")
        print("   Por favor, verifica la configuración de Firebase y los permisos.")
        return 1

    # Probar subida del archivo específico
    success, blob = test_file_upload()
    if not success:
        print("\n❌ No se puede subir el archivo al bucket.")
        print("\n" + "=" * 60)
        print("INFORMACIÓN PARA EL ADMINISTRADOR:")
        print("=" * 60)
        print("Para solucionar este problema, solicita al administrador de la cuenta")
        print("que otorgue al service account los siguientes permisos:")
        print("\n1. En Cloud Console:")
        print("   - Ve a: https://console.cloud.google.com/storage/browser")
        print("   - Selecciona el bucket: rc-proyect-84398.firebasestorage.app")
        print("   - Ve a la pestaña 'Permissions' (Permisos)")
        print(
            "   - Busca el service account: firebase-adminsdk-fbsvc@rc-proyect-84398.iam.gserviceaccount.com"
        )
        print("   - Asigna el rol 'Storage Object Admin' o 'Storage Admin'")
        print("\n2. O usa IAM:")
        print("   - Ve a: https://console.cloud.google.com/iam/admin")
        print("   - Selecciona el proyecto: rc-proyect-84398")
        print("   - Busca el service account y otórgale el rol 'Storage Object Admin'")
        print("=" * 60)
        return 1

    if success and blob:
        print("\n" + "=" * 60)
        print("✓ PRUEBA EXITOSA - ARCHIVO SUBIDO CORRECTAMENTE")
        print("=" * 60)
        print(f"\nURL del archivo subido: {blob.public_url}")

        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
