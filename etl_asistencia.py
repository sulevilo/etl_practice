import requests

import json
from pathlib import Path


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

""" #valide que coneccion de appi y carga de json funcionan correctamente
if __name__ == "__main__":
    lista_empleados = fetch_empleados() #valide que coneccion de appi y carga de json funcionan correctamente
    for emp in lista_empleados[:3]:  #solo muestro los primeros 3 para validar 
        print(emp) """



#valido que se caruguen los registros correctamente
if __name__ == "__main__":
    registros = load_registros()
    for r in registros[:5]: #muestro los primeros 5 para validar
        print(r)

