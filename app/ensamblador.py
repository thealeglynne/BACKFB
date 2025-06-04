import os
import subprocess
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ORQUESTADOR_PATH = os.path.join(BASE_DIR, "agenteOrquestador.py")

# Paths a los archivos JSON generados por cada agente
FILES = {
    "Agente Temas": "agenteTemas.json",
    "Agente Introduccion": "agenteIntroduccion.json",
    "Agente 7conceptosClave": "agente7conceptosClave.json",
    "Agente Ensayo": "agenteEnsayo.json",
    "Agente Conclusiones": "agenteConclusiones.json",
    "Agente QuizActividades": "agenteQuizActividades.json"
}

def ejecutar_orquestador():
    print("Ejecutando orquestador...")
    result = subprocess.run(
        ["python3", ORQUESTADOR_PATH],
        cwd=BASE_DIR,
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        print("\n--- ERROR ejecutando orquestador ---")
        print(result.stderr)
        print(result.stdout)
        exit(1)
    else:
        print("Orquestador ejecutado correctamente.\n")

def cargar_json_salida(path):
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except Exception as e:
            print(f"Error leyendo {path}: {e}")
            return []

def agrupar_por_tema(listas):
    temas_dict = {}
    for agente, docs in listas.items():
        for doc in docs:
            # Identificadores posibles del tema según agente
            tema = (
                doc.get("tema")
                or doc.get("nombre")
                or doc.get("nombre_curso")
                or doc.get("materia")
                or doc.get("titulo")
                or "sin_tema"
            )
            if tema not in temas_dict:
                temas_dict[tema] = {}
            temas_dict[tema][agente] = doc
    return temas_dict

def mostrar_documentos_completos(temas_por_agente):
    for tema, agentes in temas_por_agente.items():
        print("="*60)
        print(f"TEMA: {tema.upper()}")
        print("="*60)
        # Orden deseado
        orden = [
            "Agente Temas",
            "Agente Introduccion",
            "Agente 7conceptosClave",
            "Agente Ensayo",
            "Agente Conclusiones",
            "Agente QuizActividades"
        ]
        for agente in orden:
            doc = agentes.get(agente)
            print("\n" + "="*60)
            print(f"== {agente} ==")
            print("="*60)
            # Buscamos la clave de contenido relevante en cada agente:
            contenido = (
                doc.get("contenido")
                or doc.get("introduccion")
                or doc.get("conceptos_clave")
                or doc.get("ensayo")
                or doc.get("conclusiones")
                or doc.get("actividades_y_quiz")
                or json.dumps(doc, ensure_ascii=False, indent=2)
                if doc else "(Sin contenido para este agente)"
            )
            print(contenido)
            print(f"--- {agente} finalizado ---\n")
        print("\n\n")

def main():
    ejecutar_orquestador()

    # Carga todos los JSONs de los agentes
    agentes_contenido = {
        nombre: cargar_json_salida(os.path.join(BASE_DIR, archivo))
        for nombre, archivo in FILES.items()
    }
    # Agrupa todos los documentos por tema
    temas_por_agente = agrupar_por_tema(agentes_contenido)
    # Muestra cada documento compuesto por tema
    mostrar_documentos_completos(temas_por_agente)

if __name__ == "__main__":
    main()
