from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import requests
import os
import subprocess
import traceback

app = FastAPI()

# Habilitar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Variables de entorno
JSON_BIN_ID = os.getenv("JSON_BIN_ID")
JSON_BIN_API_KEY = os.getenv("JSON_BIN_API_KEY")

# Ruta absoluta del orquestador
BASE_DIR = "/opt/render/project/src/app"
ORQUESTADOR_PATH = os.path.join(BASE_DIR, "agenteOrquestador.py")

# Archivos output que quieres enviar al frontend
OUTPUT_FILES = [
    "output_AgenteTemas.txt",
    "output_AgenteIntroduccion.txt",
    "output_Agente7conceptosClave.txt",
    "output_AgenteEnsayo.txt",
    "output_AgenteConclusiones.txt",
    "output_AgenteQuizActividades.txt"
]

@app.get("/api/programa")
def get_programa():
    url = f"https://api.jsonbin.io/v3/b/{JSON_BIN_ID}/latest"
    headers = {"X-Master-Key": JSON_BIN_API_KEY}
    try:
        res = requests.get(url, headers=headers)
        res.raise_for_status()
        return res.json().get("record", {})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/temas")
def get_temas():
    try:
        temas = ["Tema 1", "Tema 2", "Tema 3"]  # Función simple para ejemplo
        return {"temas": temas}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/orquestar")
def orquestar():
    try:
        result = subprocess.run(
            ["python3", ORQUESTADOR_PATH],
            capture_output=True,
            text=True,
            cwd=BASE_DIR,
            timeout=240  # Puedes ajustar el timeout si tus agentes tardan mucho
        )
        outputs = {}
        for filename in OUTPUT_FILES:
            file_path = os.path.join(BASE_DIR, filename)
            if os.path.exists(file_path):
                with open(file_path, "r", encoding="utf-8") as f:
                    outputs[filename] = f.read()
            else:
                outputs[filename] = "(Archivo no encontrado)"
        if result.returncode != 0:
            return {
                "success": False,
                "error": result.stderr or "Error ejecutando el orquestador",
                "outputs": outputs
            }
        return {
            "success": True,
            "output": result.stdout.strip(),
            "outputs": outputs
        }
    except subprocess.TimeoutExpired:
        # Manejo especial por timeout
        return {
            "success": False,
            "error": "Tiempo de espera agotado al ejecutar el orquestador.",
            "outputs": {}
        }
    except Exception as e:
        # Devuelve SIEMPRE JSON, aun en errores inesperados
        return {
            "success": False,
            "error": str(e) + "\n" + traceback.format_exc(),
            "outputs": {}
        }
