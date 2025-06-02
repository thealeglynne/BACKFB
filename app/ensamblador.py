import subprocess
import json
import os
import time
import requests

print("\n========== Ejecutando Orquestador y todos los agentes ==========\n")
result = subprocess.run(["python", "ageneOrquestador.py"], capture_output=True, text=True)
print(result.stdout)
if result.stderr:
    print(result.stderr)

time.sleep(1)

if not os.path.exists("outputs.json"):
    print("No se encontró outputs.json. Algo falló en la ejecución del orquestador.")
    exit()

with open("outputs.json", "r", encoding="utf-8") as f:
    data = json.load(f)

materia = ""
nivel = ""
modalidad = ""
semestre = ""
intro = data.get("introduccion", "")
for linea in intro.splitlines():
    if "Materia:" in linea:
        materia = linea.replace("Materia:", "").strip()
    if "Nivel:" in linea:
        nivel = linea.replace("Nivel:", "").strip()
    if "Modalidad:" in linea:
        modalidad = linea.replace("Modalidad:", "").strip()
    if "Semestre:" in linea:
        semestre = linea.replace("Semestre:", "").strip()

reporte = []
if materia:
    reporte.append(f"{materia.upper()}")
if nivel or modalidad or semestre:
    linea_portada = " | ".join(
        [nivel if nivel else "", modalidad if modalidad else "", f"Semestre {semestre}" if semestre else ""]
    ).strip(" |")
    if linea_portada:
        reporte.append(linea_portada)
reporte.append("_" * 60)

estructura = [
    ("TEMAS PRINCIPALES", "temas"),
    ("INTRODUCCIÓN", "introduccion"),
    ("CONCEPTOS CLAVE", "conceptos_clave"),
    ("ENSAYO ACADÉMICO", "ensayo"),
    ("CONCLUSIONES", "conclusiones"),
]
for titulo, clave in estructura:
    contenido = data.get(clave, "").strip()
    if contenido:
        reporte.append(f"\n{titulo}\n{'_'*60}\n{contenido}\n")
reporte_txt = "\n".join(reporte)

with open("ReporteFinal.txt", "w", encoding="utf-8") as f:
    f.write(reporte_txt)

print("\n========== REPORTE FINAL GENERADO ==========\n")
print(reporte_txt)
print("\n========== Archivo 'ReporteFinal.txt' guardado ==========\n")

# --------- GUARDAR EN JSON BIN ---------
JSON_BIN_API_KEY = "$2a$10$TO5Moe9xid2H7DhOnwMqUuPkxgX0SZPQiQQ9f2BNiB5AFojjArd9e"  # PON AQUÍ TU API KEY REAL
JSON_BIN_ID = "6838c6bc8561e97a501d407b"

estructura_json = {
    "reporte_completo": reporte_txt,
    "materia": materia,
    "nivel": nivel,
    "modalidad": modalidad,
    "semestre": semestre,
    "fecha_generacion": time.strftime("%Y-%m-%d %H:%M:%S")
}

url = f"https://api.jsonbin.io/v3/b/{JSON_BIN_ID}"
headers = {
    "Content-Type": "application/json",
    "X-Master-Key": JSON_BIN_API_KEY,
}

try:
    res = requests.put(url, headers=headers, json=estructura_json, timeout=10)
    res.raise_for_status()
    print("\n✅ Contenido guardado en JSON Bin correctamente.")
    print("URL:", f"https://jsonbin.io/b/{JSON_BIN_ID}")
except Exception as e:
    print("❌ Error al guardar en JSON Bin:", e)
    print("Response:", getattr(e, 'response', None))
