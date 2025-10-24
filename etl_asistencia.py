import json
import requests
from pathlib import Path
import pandas as pd
from datetime import datetime, timedelta

def fetch_empleados(api_url="https://jsonplaceholder.typicode.com/users"):

    try:
        print(f"Conectando a la API: {api_url}")
        response = requests.get(api_url, timeout=5)
        response.raise_for_status()  
        empleados = response.json()  
        print(f"Datos recibidos: {len(empleados)} empleados encontrados.")
        return empleados
    except requests.exceptions.RequestException as e:
        print("Error al conectar con la API:", e)
        return []
    
def load_registros(file_path="data/registros_huellas.json"): 
    path = Path(file_path)
    if not path.exists():
        print(f"archivo no encontrado: {path}")
        return []

    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        registros_validos = []
        registros_erroneos = []

        for item in data:
            if all(k in item for k in ['cedula', 'fecha', 'hora', 'tipo']):
                registros_validos.append(item)
            else:
                registros_erroneos.append(item)

        print(f"registro cargados: {len(registros_validos)} validos, {len(registros_erroneos)} con errores.")
        return registros_validos

    except json.JSONDecodeError:
        print("error: el archivo no tiene un formato JSON valido.")
        return []
    except Exception as e:
        print("error al leer el archivo:", e)
        return []


def transformar_datos(empleados, registros):
    df_registros = pd.DataFrame(registros)
    df_empleados = pd.DataFrame(empleados)

    df_registros['fecha'] = pd.to_datetime(df_registros['fecha'])
    df_registros['hora'] = pd.to_datetime(df_registros['hora'], format="%H:%M:%S").dt.time

    resultados = []

    for _, emp in df_empleados.iterrows():
        cedula = emp["id"]
        nombre = emp["name"]
        registros_emp = df_registros[df_registros["cedula"] == cedula]

        # si el registro esta vacio osea que no asistio
        if registros_emp.empty:
            resultados.append({
                "cedula": cedula,
                "nombre": nombre,
                "hora_entrada": None,
                "hora_salida": None,
                "tiempo_trabajado": "0h 0m",
                "estado": "NO ASISTIÓ"
            })
            continue

        registros_in = registros_emp[registros_emp["tipo"] == "IN"]
        registros_out = registros_emp[registros_emp["tipo"] == "OUT"]

        hora_entrada = registros_in["hora"].min() if not registros_in.empty else None
        hora_salida = registros_out["hora"].max() if not registros_out.empty else None

        # aqui validamos los distintos criterios
        if hora_entrada and hora_salida:
            t_entrada = datetime.combine(datetime.today(), hora_entrada)
            t_salida = datetime.combine(datetime.today(), hora_salida)
            duracion = t_salida - t_entrada
            horas = duracion.seconds // 3600
            minutos = (duracion.seconds % 3600) // 60
            tiempo_str = f"{horas}h {minutos}m"
            estado = "ASISTIÓ"

            hora_limite = datetime.strptime("08:00:00", "%H:%M:%S").time()
            if hora_entrada > hora_limite:
                estado = "RETARDO"

        elif hora_entrada and not hora_salida:
            # aun en jornada
            tiempo_str = "N/A"
            estado = "EN JORNADA"

        elif hora_salida and not hora_entrada:
            #error o registro incompleto
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

    df_resultado = pd.DataFrame(resultados)
    return df_resultado

if __name__ == "__main__":
    
    lista_empleados = fetch_empleados() #valide que coneccion de appi y carga de json funcionan correctamente
    """ #valide que coneccion de appi y carga de json funcionan correctamente
    for emp in lista_empleados[:3]:  #solo muestro los primeros 3 para validar 
        print(emp)"""
    #valido que se caruguen los registros correctamente
    registros = load_registros()
    """ for r in registros[:5]: #muestro los primeros 5 para validar
        print(r)  """
    resultados = transformar_datos(lista_empleados,registros)
    print(resultados.head(5).to_string(index=False))





