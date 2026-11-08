#!/usr/bin/env python3
"""
Script de prueba para subir un solo archivo a Firebase Storage
Captura mensajes de error detallados para pedir permisos al administrador

Este script está refactorizado para separar las funciones de impresión del código principal.
"""

import os
import sys
import traceback
from typing import Optional

from firebase_admin import credentials, initialize_app, storage
from google.api_core import exceptions
from google.cloud.storage.blob import Blob

public_url = None


def print_header(title: str):
    """Imprimir encabezado del script"""
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


def print_connection_test():
    """Imprimir mensaje de prueba de conexión"""
    print("\n1. Inicializando Firebase...")
    cred = credentials.Certificate("credentials/service_account.json")
    initialize_app(cred, {"storageBucket": "rc-proyect-84398.firebasestorage.app"})
    print("   ✓ Conexión exitosa")

    # Obtener bucket
    print("\n2. Obteniendo bucket de Storage...")
    bucket = storage.bucket("rc-proyect-84398.firebasestorage.app")
    print(f"   ✓ Bucket obtenido: {bucket.name}")
    return bucket


def print_file_upload_test(local_file: str, blob_path: str):
    """Imprimir mensajes de prueba de subida de archivo"""
    print(f"\n1. Archivo local: {local_file}")
    print(f"   Bucket destino: {blob_path}")

    # Verificar archivo local
    print("\n2. Verificando archivo local...")
    if not os.path.exists(local_file):
        print(f"   ✗ El archivo no existe: {local_file}")
        return None, False
    print("   ✓ Archivo existe")

    # Obtener bucket
    print("\n3. Obteniendo bucket...")
    bucket = storage.bucket("rc-proyect-84398.firebasestorage.app")

    # Crear blob
    print("\n4. Creando blob...")
    blob = bucket.blob(blob_path)
    print(f"   ✓ Blob creado: {blob.name}")

    # Subir archivo
    print("\n5. Subiendo archivo...")
    blob.upload_from_filename(local_file)
    print("   ✓ Archivo subido exitosamente")

    # Hacer público
    print("\n6. Haciendo el archivo público...")
    blob.make_public()
    print(f"   ✓ URL pública: {blob.public_url}")

    return blob, True


def print_error_info():
    """Imprimir información de error para el administrador"""
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


def print_connection_error():
    """Imprimir mensaje de error de conexión"""
    print("\n❌ No se puede conectar a Firebase Storage.")
    print("   Por favor, verifica la configuración de Firebase y los permisos.")


def print_upload_error():
    """Imprimir mensaje de error de subida"""
    print("\n❌ No se puede subir el archivo al bucket.")


def print_success(blob):
    """Imprimir mensaje de éxito"""
    print("\n" + "=" * 60)
    print("✓ PRUEBA EXITOSA - ARCHIVO SUBIDO CORRECTAMENTE")
    print("=" * 60)
    print(f"\nURL del archivo subido: {blob.public_url}")


def test_firebase_connection() -> bool:
    """Probar conexión a Firebase Storage"""
    try:
        print_header("PRUEBA DE CONEXIÓN A FIREBASE STORAGE")
        bucket = print_connection_test()
        return True
    except Exception:
        print("\n✗ Error de conexión:")
        traceback.print_exc()
        return False


def test_file_upload() -> tuple[Optional[Blob], bool]:
    """Probar subir el archivo de prueba"""
    # Archivo específico
    local_file = "actas/departamentales/2083311.jpg"
    blob_path = "mesas/gobernatura/2083311.jpg"

    try:
        result = print_file_upload_test(local_file, blob_path)
        return result
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

    return None, False


def main():
    print_header("SCRIPT DE PRUEBA FIREBASE STORAGE")

    # Probar conexión
    if not test_firebase_connection():
        print_connection_error()
        return 1

    # Probar subida del archivo específico
    blob, success = test_file_upload()

    if not success:
        print_upload_error()
        print_error_info()
        return 1

    if success and blob:
        print_success(blob)

    return 0


if __name__ == "__main__":
    sys.exit(main())
