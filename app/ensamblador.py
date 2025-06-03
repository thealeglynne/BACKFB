import os
import subprocess

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

ORQUESTADOR_PATH = os.path.join(BASE_DIR, "agenteOrquestador.py")

OUTPUT_FILES = [
    "output_AgenteTemas.txt",
    "output_AgenteIntroduccion.txt",
    "output_Agente7conceptosClave.txt",
    "output_AgenteEnsayo.txt",
    "output_AgenteConclusiones.txt",
    "output_AgenteQuizActividades.txt"
]

def ejecutar_orquestador():
    print("Ejecutando orquestador...")
    result = subprocess.run(
        ["python3", ORQUESTADOR_PATH],
        cwd=BASE_DIR,
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        print("¡Error ejecutando el orquestador!\n")
        print(result.stderr)
        print(result.stdout)  # Por si el error está en stdout
        exit(1)
    else:
        print("Orquestador ejecutado correctamente.\n")

def mostrar_todo():
    for filename in OUTPUT_FILES:
        file_path = os.path.join(BASE_DIR, filename)
        print(f"\n{'='*60}")
        print(f"== {filename.replace('output_', '').replace('.txt','').replace('Agente','Agente ')} ==")
        print(f"{'='*60}")
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                contenido = f.read().strip()
                print(contenido if contenido else "(Archivo vacío)")
        else:
            print("(Archivo no encontrado)")

if __name__ == "__main__":
    try:
        ejecutar_orquestador()
        mostrar_todo()
    except Exception as e:
        import traceback
        print("ERROR EN ENSAMBLADOR:")
        print(traceback.format_exc())
