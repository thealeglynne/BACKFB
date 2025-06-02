import subprocess
import json
import os

AGENTES = [
    ("temas", "AgenteTemas.py"),
    ("introduccion", "AgenteIntroduccion.py"),
    ("conceptos_clave", "Agente7conceptosClave.py"),
    ("ensayo", "AgenteEnsayo.py"),
    ("conclusiones", "AgenteConclusiones.py"),
    ("quiz_actividades", "AgenteQuizActividades.py"),
]

contexto = {}

def run_agent(agente, contexto):
    # Escribe el contexto acumulado para que el agente lo lea
    with open("contexto_global.json", "w", encoding="utf-8") as f:
        json.dump(contexto, f, indent=2, ensure_ascii=False)
    # Ejecuta el agente
    result = subprocess.run(
        ["python", agente],
        capture_output=True,
        text=True
    )
    # El agente debe imprimir el contenido resultante
    return result.stdout.strip()

def main():
    for key, script in AGENTES:
        print(f"\n========== Ejecutando {script} ==========\n")
        output = run_agent(script, contexto)
        contexto[key] = output
        with open(f"output_{script.replace('.py','.txt')}", "w", encoding="utf-8") as f:
            f.write(output)
    # Guarda todo el contexto final
    with open("outputs.json", "w", encoding="utf-8") as f:
        json.dump(contexto, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    main()
