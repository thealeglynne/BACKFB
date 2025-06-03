import subprocess
import json
import os

AGENTES = [
    ("temas", "agentes/AgenteTemas.py"),
    ("introduccion", "agentes/AgenteIntroduccion.py"),
    ("conceptos_clave", "agentes/Agente7conceptosClave.py"),
    ("ensayo", "agentes/AgenteEnsayo.py"),
    ("conclusiones", "agentes/AgenteConclusiones.py"),
    ("quiz_actividades", "agentes/AgenteQuizActividades.py"),
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

# Obtiene la ruta base del script actual (agenteOrquestador.py)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def run_agent(agente_rel_path, contexto):
    # Construye la ruta absoluta al agente
    agente_path = os.path.join(BASE_DIR, agente_rel_path)
    with open(os.path.join(BASE_DIR, "contexto_global.json"), "w", encoding="utf-8") as f:
        json.dump(contexto, f, indent=2, ensure_ascii=False)
    result = subprocess.run(
        ["python", agente_path],
        capture_output=True,
        text=True
    )
    if result.stderr:
        print(f"--- ERROR en {agente_rel_path} ---\n{result.stderr}")
    if not result.stdout.strip():
        print(f"--- {agente_rel_path} no produjo ninguna salida en stdout ---")
    return result.stdout.strip()

def main():
    for key, script_rel_path in AGENTES:
        print(f"\n========== Ejecutando {script_rel_path} ==========\n")
        output = run_agent(script_rel_path, contexto)
        contexto[key] = output
        output_filename = "output_" + os.path.basename(script_rel_path).replace('.py', '.txt')
        output_path = os.path.join(BASE_DIR, output_filename)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(output)
    # Guarda el JSON final en la ruta absoluta
    with open(os.path.join(BASE_DIR, "outputs.json"), "w", encoding="utf-8") as f:
        json.dump(contexto, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    main()
