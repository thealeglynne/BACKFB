import subprocess
import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

AGENTES = [
    ("temas", os.path.join(BASE_DIR, "agentes/AgenteTemas.py")),
    ("introduccion", os.path.join(BASE_DIR, "agentes/AgenteIntroduccion.py")),
    ("conceptos_clave", os.path.join(BASE_DIR, "agentes/Agente7conceptosClave.py")),
    ("ensayo", os.path.join(BASE_DIR, "agentes/AgenteEnsayo.py")),
    ("conclusiones", os.path.join(BASE_DIR, "agentes/AgenteConclusiones.py")),
    ("quiz_actividades", os.path.join(BASE_DIR, "agentes/AgenteQuizActividades.py")),
    ("referencias_web", os.path.join(BASE_DIR, "agentes/AgenteReferenciasWeb.py")),  # <-- Aquí tu nuevo agente
]

GLOBAL_PARAMS = {
    "tono": "institucional, académico, claro y motivador",
    "nivel": "universitario",
    "modo_salida": "coherente entre secciones",
    "instrucciones_adicionales": (
        "Asegúrate de que el vocabulario, los conceptos y el estilo sean consistentes entre secciones. "
        "Si mencionas temas, conceptos o ejemplos en una sección, retómalos y profundízalos en las siguientes. "
        "Mantén las definiciones y explicaciones alineadas. Haz referencias cruzadas a secciones previas si es relevante."
    ),
}

contexto = {"global_params": GLOBAL_PARAMS}

def run_agent(agente_path, contexto):
    contexto_file = os.path.join(BASE_DIR, "contexto_global.json")
    with open(contexto_file, "w", encoding="utf-8") as f:
        json.dump(contexto, f, indent=2, ensure_ascii=False)
    result = subprocess.run(
        ["python3", agente_path],
        capture_output=True,
        text=True
    )
    if result.stderr:
        print(f"--- ERROR en {agente_path} ---\n{result.stderr}")
    if not result.stdout.strip():
        print(f"--- {agente_path} no produjo ninguna salida en stdout ---")
    return result.stdout.strip()

def main():
    for key, script_path in AGENTES:
        print(f"\n========== Ejecutando {script_path} ==========\n")
        output = run_agent(script_path, contexto)
        contexto[key] = output
        output_filename = os.path.join(BASE_DIR, "output_" + os.path.basename(script_path).replace('.py', '.txt'))
        with open(output_filename, "w", encoding="utf-8") as f:
            f.write(output)
    # Guarda todo el contexto general
    outputs_file = os.path.join(BASE_DIR, "outputs.json")
    with open(outputs_file, "w", encoding="utf-8") as f:
        json.dump(contexto, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    main()
