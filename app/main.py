from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import requests
import os

app = FastAPI()

# Habilitar CORS (ajusta el dominio en allow_origins si lo prefieres)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Usa variables de entorno
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
    # Debes definir agente_temas, aquí un ejemplo:
    # return {"temas": "Aquí iría la lógica real de agente_temas"}
    try:
        temas = agente_temas()
        return {"temas": temas}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Ejemplo mínimo para que no falle por no definir agente_temas:
def agente_temas():
    return ["Tema 1", "Tema 2", "Tema 3"]
