import json
import requests
from pathlib import Path
from datetime import datetime, time
import csv
import logging
import time as t


# ------------------------- Logger -------------------------
def configurar_logger(fecha=None, carpeta_logs="logs"):
    Path(carpeta_logs).mkdir(parents=True, exist_ok=True)
    if fecha is None:
        fecha = datetime.today()
    fecha_str = fecha.strftime("%Y%m%d_%H%M%S")
    nombre_archivo = f"log_etl_{fecha_str}.log"
    ruta_log = Path(carpeta_logs) / nombre_archivo

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(ruta_log, encoding="utf-8"),
            logging.StreamHandler()
        ]
    )

    logging.info("Logger configurado correctamente")
    return ruta_log


# ------------------------- ETL -------------------------
def fetch_empleados(api_url="https://jsonplaceholder.typicode.com/users", reintentos=3):
    for intento in range(1, reintentos + 1):
        try:
            logging.info(f"Conectando a la API: {api_url} (Intento {intento})")
            response = requests.get(api_url, timeout=5)
            response.raise_for_status()
            empleados = response.json()
            logging.info(f"Datos recibidos: {len(empleados)} empleados encontrados.")
            return empleados
        except requests.exceptions.RequestException as e:
            logging.error(f"Error en intento {intento}: {e}")
            if intento < reintentos:
                t.sleep(2)
            else:
                logging.critical("No se pudo conectar a la API tras varios intentos.")
                return []


def load_registros(file_path="data/registros_huellas.json", fecha=None):
    path = Path(file_path)
    if not path.exists():
        logging.error(f"Archivo no encontrado: {path}")
        return []

    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        registros_validos = []
        registros_erroneos = []

        for item in data:
            if all(k in item for k in ['cedula', 'fecha', 'hora', 'tipo']):
                item_fecha = datetime.strptime(item["fecha"], "%Y-%m-%d").date()
                if fecha is None or item_fecha == fecha:
                    # guardar cédula como entero
                    registros_validos.append({
                        "cedula": int(item["cedula"]),
                        "fecha": item_fecha,
                        "hora": item["hora"],
                        "tipo": item["tipo"]
                    })
            else:
                registros_erroneos.append(item)

        logging.info(f"Registros cargados: {len(registros_validos)} válidos, {len(registros_erroneos)} con errores.")
        for err in registros_erroneos:
            logging.warning(f"Registro erróneo: {err}")

        return registros_validos

    except Exception as e:
        logging.error(f"Error al leer el archivo: {e}")
        return []


def transformar_datos(empleados, registros):
    resultados = []

    # Convertir horas a objetos datetime.time
    for r in registros:
        if isinstance(r.get("hora"), str):
            r["hora"] = datetime.strptime(r["hora"], "%H:%M:%S").time()

    for emp in empleados:
        cedula = emp["id"]  # mantener entero
        nombre = emp["name"]

        registros_emp = [r for r in registros if r.get("cedula") == cedula]

        if not registros_emp:
            resultados.append({
                "cedula": cedula,
                "nombre": nombre,
                "hora_entrada": "",
                "hora_salida": "",
                "tiempo_trabajado": "0h 0m",
                "estado": "NO ASISTIÓ"
            })
            continue

        registros_in = [r for r in registros_emp if r.get("tipo") == "IN"]
        registros_out = [r for r in registros_emp if r.get("tipo") == "OUT"]

        hora_entrada = min([r["hora"] for r in registros_in], default=None)
        hora_salida = max([r["hora"] for r in registros_out], default=None)

        if hora_entrada and hora_salida:
            t_entrada = datetime.combine(datetime.today(), hora_entrada)
            t_salida = datetime.combine(datetime.today(), hora_salida)
            duracion = t_salida - t_entrada
            total_minutos = duracion.total_seconds() // 60
            horas = int(total_minutos // 60)
            minutos = int(total_minutos % 60)
            tiempo_str = f"{horas}h {minutos}m"
            estado = "ASISTIÓ"
            if hora_entrada > time(8, 0, 0):
                estado = "RETARDO"

        elif hora_entrada and not hora_salida:
            tiempo_str = "N/A"
            estado = "EN JORNADA"

        elif hora_salida and not hora_entrada:
            tiempo_str = "N/A"
            estado = "INCOMPLETO"

        else:
            tiempo_str = "0h 0m"
            estado = "NO ASISTIÓ"

        resultados.append({
            "cedula": cedula,
            "nombre": nombre,
            "hora_entrada": hora_entrada.strftime("%H:%M:%S") if hora_entrada else "",
            "hora_salida": hora_salida.strftime("%H:%M:%S") if hora_salida else "",
            "tiempo_trabajado": tiempo_str,
            "estado": estado
        })

    return resultados


def cargar_csv(resultados, fecha=None, carpeta_salida="output"):
    Path(carpeta_salida).mkdir(parents=True, exist_ok=True)
    if fecha is None:
        fecha = datetime.today()
    fecha_str = fecha.strftime("%Y%m%d")
    nombre_archivo = f"reporte_asistencia_{fecha_str}.csv"
    ruta_archivo = Path(carpeta_salida) / nombre_archivo

    campos = ["cedula", "nombre", "hora_entrada", "hora_salida", "tiempo_trabajado", "estado"]

    with ruta_archivo.open("w", encoding="utf-8", newline="") as f:
        escritor = csv.DictWriter(f, fieldnames=campos)
        escritor.writeheader()
        escritor.writerows(resultados)

    logging.info(f"Archivo CSV generado: {ruta_archivo}")
    return ruta_archivo

def log_resumen_asistencia(resultados):
    """
    Calcula y genera un resumen de asistencia usando el logger.
    """
    total_empleados = len(resultados)
    asistieron = sum(1 for r in resultados if r["estado"] in ["ASISTIÓ", "RETARDO", "EN JORNADA"])
    no_asistieron = sum(1 for r in resultados if r["estado"] == "NO ASISTIÓ")
    incompletos = sum(1 for r in resultados if r["estado"] == "INCOMPLETO")

    logging.info("===== RESUMEN DE ASISTENCIA =====")
    logging.info(f"Total empleados: {total_empleados}")
    logging.info(f"Asistieron: {asistieron}")
    logging.info(f"No asistieron: {no_asistieron}")
    logging.info(f"Incompletos: {incompletos}")
    logging.info("=================================")

# ------------------------- MAIN ETL -------------------------
if __name__ == "__main__":
    # Preguntar fecha al usuario
    fecha_input = input("Ingrese la fecha a procesar (YYYY-MM-DD) o presione Enter para hoy: ").strip()
    if fecha_input:
        try:
            fecha_obj = datetime.strptime(fecha_input, "%Y-%m-%d").date()
        except ValueError:
            print("Formato de fecha incorrecto. Se usará la fecha de hoy.")
            fecha_obj = datetime.today().date()
    else:
        fecha_obj = datetime.today().date()

    ruta_log = configurar_logger(fecha=fecha_obj)

    # Extract
    lista_empleados = fetch_empleados()
    registros = load_registros(fecha=fecha_obj)

    # Transform
    resultados = transformar_datos(lista_empleados, registros)

    # generar resumen
    log_resumen_asistencia(resultados)

    # Load
    cargar_csv(resultados, fecha=fecha_obj)
