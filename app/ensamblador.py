import os
import subprocess
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

ORQUESTADOR_PATH = os.path.join(BASE_DIR, "agenteOrquestador.py")

# Archivos de output esperados por cada agente, ubicados en la raíz
FILES = {
    "Agente Temas": "agenteTemas.json",
    "Agente Introduccion": "agenteIntroduccion.json",
    "Agente 7conceptosClave": "agente7ConceptosClave.json",
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
    print(f"Buscando archivo: {path} -> {'Existe' if os.path.exists(path) else 'NO existe'}")
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
        # Orden de los agentes en la salida
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
            if doc:
                # Busca las claves relevantes (de más específico a más general)
                for campo in ["contenido", "introduccion", "conceptos_clave", "ensayo", "conclusiones", "actividades_y_quiz"]:
                    if campo in doc and doc[campo]:
                        contenido = doc[campo]
                        break
                else:
                    contenido = json.dumps(doc, ensure_ascii=False, indent=2)
            else:
                contenido = "(Sin contenido para este agente)"
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
