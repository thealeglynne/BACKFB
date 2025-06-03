from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import requests
import os
import subprocess  # necesario para ejecutar procesos

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
        temas = agente_temas()
        return {"temas": temas}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def agente_temas():
    return ["Tema 1", "Tema 2", "Tema 3"]

# Aquí el endpoint que detecta /api/orquestar
@app.post("/api/orquestar")
def orquestar():
    try:
        # Ejecuta el script orquestador
        result = subprocess.run(
            ["python", "app/agenteOrquestador.py"],  # Ajusta la ruta si tu script está en otra carpeta
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            return {"error": result.stderr or "Error ejecutando el orquestador"}
        return {"output": result.stdout.strip()}
    except Exception as e:
        return {"error": str(e)}
