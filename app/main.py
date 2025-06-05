from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import os
import subprocess
import traceback
import uuid
import json

app = FastAPI()

# CORS igual que antes
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"]
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENSAMBLADOR_PATH = os.path.join(BASE_DIR, "ensamblador.py")
JOBS_DIR = os.path.join(BASE_DIR, "jobs")
os.makedirs(JOBS_DIR, exist_ok=True)

def run_ensamblador(job_id):
    try:
        result = subprocess.run(
            ["python3", ENSAMBLADOR_PATH],
            capture_output=True, text=True, cwd=BASE_DIR, timeout=500   
        )
        output = {
            "status": "done" if result.returncode == 0 else "error",
            "ensamblado": result.stdout.strip(),
            "error": result.stderr if result.returncode != 0 else None
        }
    except subprocess.TimeoutExpired:
        output = {"status": "error", "error": "Timeout", "ensamblado": ""}
    except Exception as e:
        output = {"status": "error", "error": str(e) + "\n" + traceback.format_exc(), "ensamblado": ""}

    with open(os.path.join(JOBS_DIR, f"{job_id}.json"), "w") as f:
        json.dump(output, f)

@app.post("/api/ensamblar")
async def crear_job(background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    # crea un archivo con status "processing"
    with open(os.path.join(JOBS_DIR, f"{job_id}.json"), "w") as f:
        json.dump({"status": "processing"}, f)
    # lanza la tarea en segundo plano
    background_tasks.add_task(run_ensamblador, job_id)
    return {"jobId": job_id}

@app.get("/api/ensamblar/estado")
def estado_job(jobId: str):
    job_file = os.path.join(JOBS_DIR, f"{jobId}.json")
    if not os.path.isfile(job_file):
        return {"status": "not_found"}
    with open(job_file, "r") as f:
        data = json.load(f)
    return data
