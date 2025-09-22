import asyncio
import base64
import os
import random
from typing import Dict, List, Optional

import aiohttp
import pandas as pd

API_URL = "https://computo.oep.org.bo/api/v1/resultados/mesa"
CSV_FILE = "resultados.csv"
OUTPUT_DIR = "actas"


async def fetch_mesa_data(
    session: aiohttp.ClientSession, codigo_mesa: int
) -> Optional[Dict]:
    """Realiza una consulta al endpoint de la OEP para obtener datos de una mesa específica."""
    try:
        payload = {"codigoMesa": codigo_mesa}
        async with session.post(API_URL, json=payload) as response:
            if response.status == 200:
                return await response.json()
            else:
                print(f"Error {response.status} al consultar la mesa {codigo_mesa}")
                return None
    except Exception as e:
        print(f"Excepción al consultar la mesa {codigo_mesa}: {str(e)}")
        return None


def save_acta_image(codigo_mesa: int, base64_data: str) -> bool:
    """Guarda la imagen del acta en formato JPEG usando el código de mesa como nombre de archivo."""
    try:
        # Decodificar los datos base64
        image_data = base64.b64decode(base64_data)

        # Crear la ruta completa del archivo
        filename = f"{codigo_mesa}.jpg"
        filepath = os.path.join(OUTPUT_DIR, filename)

        # Guardar la imagen
        with open(filepath, "wb") as f:
            f.write(image_data)

        print(f"Acta guardada: {filepath}")
        return True
    except Exception as e:
        print(f"Error al guardar la imagen para la mesa {codigo_mesa}: {str(e)}")
        return False


async def process_mesa(session: aiohttp.ClientSession, codigo_mesa: int) -> bool:
    """Procesa una mesa individual: consulta la API y guarda la imagen del acta si existe."""
    print(f"Procesando mesa: {codigo_mesa}")

    # Consultar la API
    data = await fetch_mesa_data(session, codigo_mesa)
    if not data:
        return False

    # Buscar el adjunto de tipo ACTA
    adjuntos = data.get("adjunto", [])
    acta_adjunto = next((adj for adj in adjuntos if adj.get("tipo") == "ACTA"), None)

    if not acta_adjunto:
        print(f"No se encontró acta para la mesa {codigo_mesa}")
        return False

    # Obtener el valor base64
    base64_data = acta_adjunto.get("valor")
    if not base64_data:
        print(f"El acta de la mesa {codigo_mesa} no contiene datos válidos")
        return False

    # Guardar la imagen
    return save_acta_image(codigo_mesa, base64_data)


async def load_mesa_codes_from_csv() -> List[int]:
    """Carga los códigos de mesa desde el archivo CSV."""
    df = pd.read_csv(CSV_FILE)
    df = df[df["Descripcion"] == "PRESIDENTE"]
    mesa_codes = [int(code) for code in df["CodigoMesa"].tolist()]

    downloaded_codes = {
        int(filename.split(".")[0]) for filename in os.listdir(OUTPUT_DIR)
    }
    mesa_codes = [code for code in mesa_codes if code not in downloaded_codes]
    random.shuffle(mesa_codes)

    print(f"Actas descargadas: {len(downloaded_codes)}")
    print(f"Se van a descargar {len(mesa_codes)} actas...")

    return mesa_codes


async def main():
    """Función principal que coordina todo el proceso."""
    # Crear directorio de salida si no existe
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Cargar códigos de mesa
    mesa_codes = await load_mesa_codes_from_csv()
    if not mesa_codes:
        print("No se encontraron códigos de mesa para procesar")
        return

    print(f"Procesando {len(mesa_codes)} mesas...")

    connector = aiohttp.TCPConnector(
        limit=100,
        limit_per_host=50,
        ttl_dns_cache=300,
        use_dns_cache=True,
    )

    timeout = aiohttp.ClientTimeout(total=30)

    async with aiohttp.ClientSession(
        connector=connector,
        timeout=timeout,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            )
        },
    ) as session:
        semaphore = asyncio.Semaphore(10)

        async def process_with_semaphore(codigo_mesa):
            async with semaphore:
                result = await process_mesa(session, codigo_mesa)
                # Agregar un pequeño retraso entre solicitudes
                await asyncio.sleep(0.5)
                return result

        results = await asyncio.gather(
            *[process_with_semaphore(code) for code in mesa_codes],
            return_exceptions=True,
        )

        success_count = sum(
            1 for r in results if r is True and not isinstance(r, Exception)
        )
        print(
            f"Proceso completado. {success_count}/{len(mesa_codes)} mesas procesadas exitosamente."
        )


if __name__ == "__main__":
    asyncio.run(main())
