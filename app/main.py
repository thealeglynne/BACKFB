from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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

# Usar ruta relativa, funciona tanto local como en producción
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENSAMBLADOR_PATH = os.path.join(BASE_DIR, "ensamblador.py")

@app.post("/api/ensamblar")
def ensamblar():
    try:
        result = subprocess.run(
            ["python3", ENSAMBLADOR_PATH],
            capture_output=True,
            text=True,
            cwd=BASE_DIR,
            timeout=300
        )
        if result.returncode != 0:
            # Mostrar ambos: stderr y stdout, para ver el error completo
            return {
                "success": False,
                "error": (result.stderr + "\n" + result.stdout) if (result.stderr or result.stdout) else "Error ejecutando el ensamblador",
                "ensamblado": ""
            }
        return {
            "success": True,
            "ensamblado": result.stdout.strip()
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "Tiempo de espera agotado al ejecutar el ensamblador.",
            "ensamblado": ""
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e) + "\n" + traceback.format_exc(),
            "ensamblado": ""
        }
