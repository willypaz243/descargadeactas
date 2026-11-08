import asyncio
import base64
import csv
import io
import os
import random
import zipfile
from typing import Optional

import aiohttp
import pandas as pd
import requests
import xmltodict

API_URL = "https://computo.oep.org.bo/api/v1"
SUB_ACTAS_FOLDER = "subnational_actas_2da_vuelta"
DEPARTAMENTS = [
    {
        "name": "Santa Cruz",
        "id": 7,
        "folder_name": "santa_cruz",
    },
    {
        "name": "Beni",
        "id": 8,
        "folder_name": "beni",
    },
    {
        "name": "Chuquisaca",
        "id": 1,
        "folder_name": "chuquisaca",
    },
    # {
    #     "name": "Cochabamba",
    #     "id": 3,
    #     "folder_name": "cochabamba",
    # },
    # {
    #     "name": "La Paz",
    #     "id": 2,
    #     "folder_name": "la_paz",
    # },
    {
        "name": "Oruro",
        "id": 4,
        "folder_name": "oruro",
    },
    # {
    #     "name": "Pando",
    #     "id": 9,
    #     "folder_name": "pando",
    # },
    # {
    #     "name": "Potosí",
    #     "id": 5,
    #     "folder_name": "potosi",
    # },
    {
        "name": "Tarija",
        "id": 6,
        "folder_name": "tarija",
    },
]


def load_downloaded_acta_codes() -> list[list[str]]:
    """Carga los códigos de actas ya descargados desde un archivo CSV.

    Crea el directorio de salida si no existe y el archivo CSV si no existe.
    Si el archivo no existe, se crea con el encabezado correspondiente.

    Returns:
        list[list[str]]: Lista de filas del CSV, donde cada fila es una lista de strings
                         con el código de mesa y la ruta del archivo.
    """
    os.makedirs(SUB_ACTAS_FOLDER, exist_ok=True)
    filename = f"{SUB_ACTAS_FOLDER}/downloaded.csv"
    if not os.path.exists(filename):
        header = ["mesa_code", "filepath"]
        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(header)
        return [header]

    with open(filename, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        return list(reader)


downloaded_actas = load_downloaded_acta_codes()


async def download_excel(departament_id: int) -> tuple[str, bytes]:
    """Descarga el archivo Excel de resultados del departamento especificado.

    Realiza una solicitud POST al endpoint de la API de la OEP para obtener
    los datos del departamento en formato Excel codificado en base64.

    Args:
        departament_id (int): El ID numérico del departamento.

    Returns:
        tuple[str, bytes]: Una tupla que contiene el nombre del archivo Excel
                           y los bytes decodificados del archivo.

    Raises:
        ValueError: Si no se encuentra el archivo en la respuesta de la API.
        requests.HTTPError: Si la solicitud HTTP falla.
    """
    payload = {"tipoArchivo": "excel", "idDepartamento": departament_id}
    response = requests.post(f"{API_URL}/descargar", json=payload)
    response.raise_for_status()
    data = response.json()
    base64_string = data.get("archivo")
    file_name = data.get("nombreArchivo")
    if not base64_string:
        raise ValueError("No se encontró el archivo en la respuesta")
    decoded_bytes = base64.b64decode(base64_string)
    return file_name, decoded_bytes


async def extract_datafram_from_bytes(excel_bytes: bytes) -> pd.DataFrame:
    """Extrae datos de un archivo Excel binario analizando su estructura XML interna.

    Lee directamente el archivo ZIP del Excel, parsea el XML del libro de trabajo
    y de las hojas para extraer los datos sin usar pandas directamente para la
    lectura inicial, permitiendo un control más fino sobre la extracción de
    encabezados y datos numéricos.

    Args:
        excel_bytes (bytes): Los bytes del archivo Excel.

    Returns:
        pd.DataFrame: Un DataFrame de pandas con los datos extraídos, incluyendo
                      una columna 'Hoja' que indica el nombre de la hoja de origen.
    """
    excel_file = io.BytesIO(excel_bytes)
    with zipfile.ZipFile(excel_file, "r") as z:
        workbook_xml = z.read("xl/workbook.xml")
        workbook_dict = xmltodict.parse(workbook_xml)
        sheets = workbook_dict["workbook"]["sheets"]["sheet"]
        collection = sheets
        if isinstance(sheets, dict):
            collection = [sheets]
        all_data = []
        for sheet in collection:
            sheet_name = sheet["@name"]
            sheet_id = sheet["@sheetId"]
            sheet_xml = z.read(f"xl/worksheets/sheet{sheet_id}.xml")
            sheet_dict = xmltodict.parse(sheet_xml)
            sheet_data = sheet_dict["worksheet"]["sheetData"]
            rows = sheet_data.get("row", [])
            if isinstance(rows, dict):
                rows = [rows]
            headers = []
            data_rows = []
            for row in rows:
                row_num = int(row["@r"])
                data_row = []
                if row_num == 1:  # Header
                    for cell in row.get("c", [])[:16]:
                        cell_ref = cell["@r"]
                        header_name = cell_ref[:-1]
                        value = cell.get("v")
                        if value is not None:
                            headers.append(value)
                        else:
                            headers.append(f"Col_{header_name}")
                else:
                    for cell in row.get("c", [])[:16]:
                        value = cell.get("v")
                        if value is not None:
                            data_row.append(value)
                        else:
                            data_row.append(None)
                    if len(data_row) > 0 and str(data_row[0]).isnumeric():
                        data_rows.append(data_row)

            df_sheet = pd.DataFrame(data_rows, columns=headers)
            df_sheet["Hoja"] = sheet_name
            all_data.append(df_sheet)
        df_final = pd.concat(all_data, ignore_index=True)
        df_final.reset_index(drop=True, inplace=True)
        return df_final


async def load_mesa_codes_from_csv(dataframe: pd.DataFrame) -> list[int]:
    """Carga los códigos de mesa del DataFrame, excluyendo los ya descargados.

    Filtra los códigos de mesa presentes en el DataFrame proporcionado,
    eliminando aquellos que ya están registrados en la lista global
    `downloaded_actas`. Mezcla los códigos restantes aleatoriamente.

    Args:
        dataframe (pd.DataFrame): DataFrame que contiene la columna 'CodigoMesa'.

    Returns:
        list[int]: Lista de códigos de mesa que no han sido descargados previamente,
                   mezclados aleatoriamente.
    """
    global downloaded_actas
    mesa_codes = [int(code) for code in dataframe["CodigoMesa"].tolist()]
    downloaded_codes = {int(c[0]) for c in downloaded_actas[1:]}
    mesa_codes = [code for code in mesa_codes if code not in downloaded_codes]
    random.shuffle(mesa_codes)
    return mesa_codes


async def fetch_mesa_data(
    session: aiohttp.ClientSession, mesa_code: int
) -> Optional[dict]:
    """Realiza una consulta al endpoint de la OEP para obtener datos de una mesa específica.

    Intenta obtener los datos de la acta de la mesa indicada. Maneja errores
    de red y de estado HTTP.
    Args:
        session (aiohttp.ClientSession): La sesión de conexión HTTP activa.
        mesa_code (int): El código numérico de la mesa de votación.

    Returns:
        Optional[dict]: Un diccionario con los datos de la mesa si la consulta
                        es exitosa, o None si ocurre un error.
    """
    try:
        url = f"{API_URL}/actas/{mesa_code}"
        async with session.get(url) as response:
            if response.status == 200:
                return await response.json()
            else:
                print(f"Error {response.status} al consultar la mesa {mesa_code}")
                return None
    except Exception as e:
        print(f"Excepción al consultar la mesa {mesa_code}: {str(e)}")
        return None


def save_acta_image(mesa_code: int, base64_data: str, folder: str) -> str | None:
    """Guarda la imagen del acta en formato JPEG usando el código de mesa como nombre de archivo.

    Decodifica los datos base64, crea el directorio correspondiente si no existe,
    guarda la imagen y registra la descarga en el archivo CSV de seguimiento.

    Args:
        mesa_code (int): El código de la mesa de votación.
        base64_data (str): Los datos de la imagen en formato base64.
        folder (str): La ruta relativa al subdirectorio donde se guardará la imagen.

    Returns:
        str | None: La ruta completa del archivo guardado si tiene éxito, o None si falla.
    """
    try:
        # Decodificar los datos base64
        image_data = base64.b64decode(base64_data)

        # Crear la ruta completa del archivo
        filename = f"{mesa_code}.jpg"
        folder = os.path.join(SUB_ACTAS_FOLDER, folder)
        os.makedirs(folder, exist_ok=True)
        filepath = os.path.join(folder, filename)
        # Guardar la imagen
        with open(filepath, "wb") as f:
            f.write(image_data)

        # Guardar registro
        with open(
            f"{SUB_ACTAS_FOLDER}/downloaded.csv", "a", newline="", encoding="utf-8"
        ) as f:
            writer = csv.writer(f)
            writer.writerow([mesa_code, filepath])

        print(f"Acta guardada: {filepath}")
        return filepath
    except Exception as e:
        print(f"Error al guardar la imagen para la mesa {mesa_code}: {str(e)}")
        return None


async def process_mesa(
    session: aiohttp.ClientSession,
    mesa_code: int,
    departament_folder: str,
) -> str | None:
    """Procesa una mesa individual: consulta la API y guarda la imagen del acta si existe.

    Obtiene los datos de la mesa, determina la carpeta de destino (Gobernatura o Alcaldía)
    según el tipo de cargo, y guarda la imagen adjunta si está disponible.

    Args:
        session (aiohttp.ClientSession): La sesión de conexión HTTP activa.
        mesa_code (int): El código de la mesa de votación.
        departament_folder (str): El nombre de la carpeta del departamento.

    Returns:
        str | None: La ruta del archivo guardado si tiene éxito, o None si no se encuentra
                    el acta o ocurre un error.
    """
    print(f"Procesando mesa: {mesa_code}")

    # Consultar la API
    data = await fetch_mesa_data(session, mesa_code)
    if not data:
        return None

    # Buscar el adjunto de tipo ACTA
    adjuntos = data.get("adjunto", [])
    acta_adjunto = next((adj for adj in adjuntos if adj.get("tipo") == "ACTA"), None)
    cabecera_fields = data.get("cabecera", {}).get("fields", [])

    folder = "gobernatura"

    if "CONCEJALES" in cabecera_fields or "ALCALDESA/ALCALDE" in cabecera_fields:
        folder = "alcaldía"

    if not acta_adjunto:
        print(f"No se encontró acta para la mesa {mesa_code}")
        return None

    # Obtener el valor base64
    base64_data = acta_adjunto.get("valor")
    if not base64_data:
        print(f"El acta de la mesa {mesa_code} no contiene datos válidos")
        return None

    # Guardar la imagen
    folder_path = f"{folder}/{departament_folder}"
    return save_acta_image(mesa_code, base64_data, folder_path)


async def download_actas(codes: list[int], departament: dict) -> list[str]:
    """Descarga las actas de una lista de códigos de mesa para un departamento específico.

    Utiliza concurrencia asíncrona con un semáforo para limitar el número de
    conexiones simultáneas. Procesa cada código de mesa y recopila las rutas
    de los archivos guardados exitosamente.

    Args:
        codes (list[int]): Lista de códigos de mesa a procesar.
        departament (dict): Diccionario con información del departamento ('folder_name', 'name').

    Returns:
        list[str]: Lista de rutas de archivos de actas guardadas exitosamente.
    """
    folder = departament["folder_name"]
    departament_name = departament["name"]
    connector = aiohttp.TCPConnector(
        limit=25,
        limit_per_host=10,
        ttl_dns_cache=300,
        use_dns_cache=True,
    )
    timeout = aiohttp.ClientTimeout(total=60)

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
        semaphore = asyncio.Semaphore(5)

        async def process_with_semaphore(mesa_code):
            async with semaphore:
                result = await process_mesa(session, mesa_code, folder)
                # Agregar un pequeño retraso entre solicitudes
                await asyncio.sleep(0.5)
                return result

        results = await asyncio.gather(
            *[process_with_semaphore(code) for code in codes],
            return_exceptions=True,
        )
        file_paths = [r for r in results if isinstance(r, str)]
        success_count = len(file_paths)
        print(
            f"Proceso completado. {success_count}/{len(codes)} mesas procesadas exitosamente.",
            f"En el departamento de {departament_name}",
        )
    return file_paths


async def main():
    """Punto de entrada principal para el script de descarga de actas.

    Itera sobre los departamentos, descarga el Excel de resultados, extrae los
    códigos de mesa pendientes y descarga las actas correspondientes.
    """
    os.makedirs(SUB_ACTAS_FOLDER, exist_ok=True)
    # random.shuffle(DEPARTAMENTS)
    # print(DEPARTAMENTS)
    for departament in DEPARTAMENTS:
        file_name, excel_bytes = await download_excel(departament["id"])
        df = await extract_datafram_from_bytes(excel_bytes)
        codes = await load_mesa_codes_from_csv(df)
        await download_actas(codes, departament)


if __name__ == "__main__":
    asyncio.run(main())
