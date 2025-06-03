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

def run_agent(agente, contexto):
    with open("contexto_global.json", "w", encoding="utf-8") as f:
        json.dump(contexto, f, indent=2, ensure_ascii=False)
    result = subprocess.run(
        ["python", agente],
        capture_output=True,
        text=True
    )
    if result.stderr:
        print(f"--- ERROR en {agente} ---\n{result.stderr}")
    if not result.stdout.strip():
        print(f"--- {agente} no produjo ninguna salida en stdout ---")
    return result.stdout.strip()

def main():
    for key, script in AGENTES:
        print(f"\n========== Ejecutando {script} ==========\n")
        output = run_agent(script, contexto)
        contexto[key] = output
        # CORREGIDO: usa solo el nombre base para guardar el output
        output_filename = "output_" + os.path.basename(script).replace('.py', '.txt')
        with open(output_filename, "w", encoding="utf-8") as f:
            f.write(output)
    with open("outputs.json", "w", encoding="utf-8") as f:
        json.dump(contexto, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    main()
