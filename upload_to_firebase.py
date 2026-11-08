#!/usr/bin/env python3
"""
Script para subir actas a Firebase Storage
Estructura de destino en Firebase Storage:
- mesas/{nro_acta}/{nro_acta}.jpg (para municipales)
- mesas/departamentales/{nro_acta}.jpg (para departamentales)
"""

import json
import os
from datetime import datetime
from pathlib import Path

import firebase_admin
from firebase_admin import credentials, storage


class FirebaseUploader:
    """Clase para gestionar la subida de actas a Firebase Storage"""

    def __init__(self, firebase_config_path=None):
        """
        Inicializa la conexión a Firebase

        Args:
            firebase_config_path: Ruta al archivo de configuración JSON de Firebase
        """
        # Buscar archivo de configuración si no se proporciona
        if firebase_config_path is None:
            firebase_config_path = self._find_firebase_config()

        if firebase_config_path and os.path.exists(firebase_config_path):
            try:
                cred = credentials.Certificate(firebase_config_path)
                firebase_admin.initialize_app(
                    cred, {"storageBucket": "rc-proyect-84398.firebasestorage.app"}
                )
                print("✓ Conexión a Firebase Storage establecida")
                print(f"  Archivo de configuración: {firebase_config_path}")
            except Exception as e:
                print(f"✗ Error al inicializar Firebase: {str(e)}")
                print("  El script continuará en modo demostración")
        else:
            print(
                "⚠ No se encontró archivo de configuración. Subida en modo demostración."
            )

    def _find_firebase_config(self):
        """Busca archivos de configuración de Firebase"""
        # Posibles nombres de archivos (las credenciales nunca se suben a git)
        possible_files = [
            "credentials/service_account.json",
            "credentials/firebase_credentials.json",
            "firebase_credentials.json",
            "service_account.json",
            "firebase.json",
            ".firebase/credentials.json",
            "firebase-adminsdk.json",
        ]

        # Buscar en directorios comunes
        search_paths = [os.getcwd(), os.path.dirname(os.path.abspath(__file__))]

        for search_path in search_paths:
            for filename in possible_files:
                filepath = os.path.join(search_path, filename)
                if os.path.exists(filepath):
                    # Verificar si es un JSON válido
                    try:
                        with open(filepath, "r") as f:
                            json.load(f)
                        return filepath
                    except:
                        pass

        return None

    def format_mesa_id(self, mesa_number):
        """
        Formatea el número de mesa a 6 dígitos

        Args:
            mesa_number: Número de mesa (puede ser string o int)

        Returns:
            str: ID formateado con 6 dígitos
        """
        return str(mesa_number).zfill(6)

    def upload_file(self, local_path, blob_path):
        """
        Sube un archivo a Firebase Storage

        Args:
            local_path: Ruta local del archivo
            blob_path: Ruta en Firebase Storage

        Returns:
            bool: True si se subió exitosamente, False en caso contrario
        """
        try:
            # Verificar que el archivo local existe
            if not os.path.exists(local_path):
                print(f"✗ El archivo no existe: {local_path}")
                return False

            # Obtener el bucket de Firebase Storage
            bucket = storage.bucket()

            # Crear la referencia del blob
            blob = bucket.blob(blob_path)

            # Subir el archivo
            blob.upload_from_filename(local_path)
            blob.make_public()  # Hacer el archivo público

            # Obtener la URL pública
            public_url = blob.public_url

            print(f"✓ Subido exitosamente: {blob_path}")
            if not isinstance(public_url, str) or len(public_url) < 50:
                print(f"  URL: {public_url}")

            return True

        except Exception as e:
            print(f"✗ Error al subir {local_path}: {str(e)}")
            return False

    def process_directory(self, source_dir, target_type):
        """
        Procesa un directorio y sube sus archivos a Firebase Storage

        Args:
            source_dir: Directorio de origen con los archivos .jpg
            target_type: Tipo de acta ('departamental' o 'municipal')

        Returns:
            dict: Estadísticas de subida
        """
        stats = {"success": 0, "failed": 0, "total": 0}

        print(f"\n{'=' * 60}")
        print(f"Procesando directorio: {source_dir}")
        print(f"Tipo: {target_type}")
        print(f"{'=' * 60}")

        # Verificar que el directorio existe
        if not os.path.exists(source_dir):
            print(f"✗ El directorio no existe: {source_dir}")
            return stats

        # Obtener todos los archivos .jpg
        files = list(Path(source_dir).glob("*.jpg"))

        if not files:
            print("✗ No se encontraron archivos .jpg")
            return stats

        print(f"\nEncontrados {len(files)} archivos .jpg")

        # Procesar cada archivo
        for file_path in files:
            # Obtener el número de acta desde el nombre del archivo
            filename = file_path.stem  # Nombre sin extensión

            # Formatear el ID de mesa a 6 dígitos
            mesa_id = self.format_mesa_id(filename)

            # Definir las rutas de destino según el tipo
            if target_type == "departamental":
                # Para departamentales: mesas/departamentales/{nro_acta}.jpg
                blob_path = f"mesas/departamentales/{filename}.jpg"
            else:  # municipal
                # Para municipales: mesas/{nro_acta}/{nro_acta}.jpg
                blob_path = f"mesas/{filename}/{filename}.jpg"

            print(f"\nProcesando: {filename}")

            # Subir el archivo
            success = self.upload_file(str(file_path), blob_path)

            if success:
                stats["success"] += 1
                stats["total"] += 1
            else:
                stats["failed"] += 1

            # Pequeña pausa para no saturar la API
            import time

            time.sleep(0.5)

        return stats

    def batch_upload(self, directories):
        """
        Procesa múltiples directorios

        Args:
            directories: Lista de tuplas (directorio, tipo)

        Returns:
            dict: Estadísticas totales
        """
        total_stats = {"success": 0, "failed": 0, "total": 0}

        print("\n" + "=" * 60)
        print("INICIO DE PROCESO DE SUBIDA")
        print("=" * 60)

        start_time = datetime.now()

        for source_dir, target_type in directories:
            stats = self.process_directory(source_dir, target_type)
            total_stats["success"] += stats["success"]
            total_stats["failed"] += stats["failed"]
            total_stats["total"] += stats["total"]

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        print("\n" + "=" * 60)
        print("RESUMEN")
        print("=" * 60)
        print(f"Total de archivos: {total_stats['total']}")
        print(f"Éxitosos: {total_stats['success']}")
        print(f"Fallidos: {total_stats['failed']}")
        print(f"Tiempo: {duration:.2f} segundos")
        print("=" * 60)

        return total_stats


def main():
    """Función principal"""

    # Crear el uploader
    uploader = FirebaseUploader()

    # Definir los directorios a procesar
    directories = [
        ("actas/departamentales", "departamental"),
        ("actas/municipales", "municipal"),
    ]

    # Procesar todos los directorios
    uploader.batch_upload(directories)


if __name__ == "__main__":
    main()
