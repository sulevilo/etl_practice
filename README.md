# Proyecto ETL: Reporte Diario de Asistencia

## 1. Descripción del proyecto
Este proyecto automatiza la generación de reportes diarios de asistencia a partir de registros biométricos. Fue desarrollado para resolver el problema que enfrenta el departamento de Recursos Humanos de **Parcial S.A.S.**, donde actualmente se requiere revisar manualmente los registros de huellas de los empleados para calcular horarios, ausencias, retardos y tiempo trabajado.

El proyecto integra datos de dos fuentes:  
- **API de empleados**: obtiene la lista oficial de empleados.  
- **Archivo local de registros biométricos**: JSON generado por el sistema de control de acceso.  

El ETL transforma y valida los datos, calcula los horarios, determina el estado de asistencia y genera un reporte diario en CSV, además de registrar logs detallados.

---

## 2. Problemática
- El sistema biométrico genera registros crudos que requieren procesamiento manual.  
- La falta de integración entre la API de empleados y los registros biométricos genera retrabajo.  
- Calcular manualmente los tiempos de entrada, salida y duración de jornada consume horas y es propenso a errores.  
- No se generan reportes automáticos, lo que dificulta auditorías y nómina.

---

## 3. Solución
Se implementó un **ETL en Python** que realiza las siguientes acciones:

### Extract (Extracción)
- Conecta a la API de empleados y obtiene su lista.  
- Lee registros biométricos locales en formato JSON.  
- Filtra los registros por fecha y valida los campos requeridos: cédula, fecha, hora y tipo de evento.

### Transform (Transformación)
- Convierte las horas a objetos `datetime.time`.  
- Agrupa registros por empleado.  
- Calcula:  
  - Hora de entrada (mínima tipo IN)  
  - Hora de salida (máxima tipo OUT)  
  - Tiempo trabajado  
  - Estado de asistencia: `ASISTIÓ`, `RETARDO`, `EN JORNADA`, `INCOMPLETO`, `NO ASISTIÓ`  
- Maneja casos especiales (solo IN o solo OUT).

### Load (Carga)
- Genera un archivo CSV diario en `output/` con las columnas:  
  `cedula`, `nombre`, `hora_entrada`, `hora_salida`, `tiempo_trabajado`, `estado`  
- Registra todos los pasos y posibles errores en un log dentro de `logs/`.

---

## 4. Estructura del proyecto
proyecto_asistencia/  
├─ data/ → `registros_huellas.json`  
├─ logs/ → logs generados por ejecución  
├─ output/ → reportes CSV generados  
├─ etl_asistencia.py → script principal del ETL  
└─ requirements.txt → dependencias (`requests`)  

---

## 5. Requisitos
- Python 3.8 o superior  
- Librerías externas: `requests`  
- Librerías estándar: `json`, `csv`, `datetime`, `pathlib`, `logging`, `time`  

**requirements.txt**:  
requests  

---

## 6. Instalación y ejecución
1. Clonar el repositorio:  
`git clone https://github.com/sulevilo/etl_practice.git`  
`cd etl_practice`  

2. Instalar dependencias:  
`pip install -r requirements.txt`  

3. Crear carpetas necesarias si no existen:  
`mkdir -p data output logs`  

4. Colocar `registros_huellas.json` en la carpeta `data/`.  

5. Ejecutar el ETL:  
`python etl_asistencia.py`  

- Ingresar la fecha en formato `YYYY-MM-DD` o presionar Enter para usar la fecha actual.  
- Se generarán los archivos:  
  - CSV con reporte diario en `output/`  
  - Log detallado en `logs/`  

---

## 7. Resultados esperados
- **Reporte CSV**: cada empleado con hora de entrada, salida, tiempo trabajado y estado de asistencia.
- **Logs**: seguimiento de errores, registros incompletos, conexiones a la API y resumen de asistencia.

![Ejemplo de ejecución](images/captura_ejecucion.png)
<img width="1920" height="1020" alt="captura_ejecucion" src="https://github.com/user-attachments/assets/7b57a535-4771-4f57-9aaf-d1b21b95421b" />


- Detección automática de retardos, ausencias y registros incompletos.
- Proceso repetible y confiable para cualquier fecha.


---
