import os
import requests
import json
import sys
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from langchain.chains import LLMChain

# ==============================
# CONFIGURACIÓN DIRECTA DE CLAVES Y CONSTANTES

GROQ_API_KEY = "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"
SERPER_API_KEY = "5f7dbe7e7ce70029c6cddd738417a3e4132d6e47"
JSON_BIN_ID = "682f27e08960c979a59f5afe"
JSON_BIN_API_KEY = "$2a$10$CWeZ66JKpedXMgIy/CDyYeEoH18x8tgxZDNBGDeHRSAusOVtHrwce"
CONTEXTO_GLOBAL_FILE = "contexto_global.json"

# ==============================
# LLM Configuration
llm = ChatGroq(
    model_name="llama3-70b-8192", 
    api_key=GROQ_API_KEY,
    temperature=0.38,  # Un poco más creativo que el original pero sigue siendo académico
    max_tokens=2000
)

def leer_contexto_global():
    if os.path.exists(CONTEXTO_GLOBAL_FILE):
        with open(CONTEXTO_GLOBAL_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                print(f"Advertencia: {CONTEXTO_GLOBAL_FILE} contiene JSON inválido. Se devuelve contexto vacío.")
                return {}
    return {}

def fetch_course_data():
    url = f"https://api.jsonbin.io/v3/b/{JSON_BIN_ID}/latest"
    headers = {"X-Master-Key": JSON_BIN_API_KEY}
    try:
        res = requests.get(url, headers=headers, timeout=10)
        res.raise_for_status()
        data = res.json()
        record = data.get("record")
        if record is None:
            if isinstance(data, dict) and "Nombre del Programa" in data:
                record = data
            elif isinstance(data, list) and data:
                record = data[-1]
                if not isinstance(record, dict):
                    print(f"Advertencia: El último elemento del JSON Bin no es un diccionario: {record}")
                    return None
            else:
                print(f"Error: La respuesta del JSON Bin no contiene la clave 'record' ni es el registro directamente. Respuesta: {data}")
                return None
        if isinstance(record, list):
            return record[-1] if record else None
        elif isinstance(record, dict):
            return record
        else:
            print(f"Error: El contenido de 'record' no es una lista ni un diccionario: {type(record)}")
            return None
    except Exception as e:
        print(f"Error inesperado al obtener datos del curso: {e}")
    return None

def search_web_serper(query, limit_organic=3):
    url = "https://google.serper.dev/search"
    headers = {"X-API-KEY": SERPER_API_KEY, "Content-Type": "application/json"}
    data = {"q": query}
    try:
        response = requests.post(url, headers=headers, json=data, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception:
        return {"error": "No se pudo realizar la búsqueda"}

def get_best_snippets(serper_response, limit=5):
    if not serper_response or "organic" not in serper_response:
        return ""
    snippets = [r.get("snippet", "") for r in serper_response["organic"] if r.get("snippet")]
    return "\n".join(snippets[:limit])

# === PROMPT DEL AGENTE ===
conceptos_clave_prompt_template = PromptTemplate(
     input_variables=["nombre_curso", "nivel_estudios", "tema", "context_web", "contexto_previos", "conceptos_previos"],
    template=(
        "Actúa como académico universitario experto en educación y divulgación didáctica. "
        "Desarrolla la sección 'Conceptos clave' para el tema '{tema}' dentro de la unidad del curso '{nombre_curso}' para estudiantes de {nivel_estudios}.\n\n"
        "INSTRUCCIONES OBLIGATORIAS:\n"
        "- Elabora una lista de SIETE (7) conceptos clave absolutamente esenciales para comprender profundamente este tema. "
        "Cada concepto debe tener un título breve (máximo 3 palabras), original, claro y diferente de los usados en otros temas (evita repeticiones del bloque 'conceptos_previos').\n"
        "- Para cada concepto, escribe el nombre en **negrita** seguido de dos puntos (ejemplo: **Pensamiento Computacional:**).\n"
        "- Desarrolla un único párrafo explicativo de al menos 6 líneas, redactado en lenguaje claro, profesional y didáctico. "
        "La explicación debe ser relevante, profunda y original. Explica el concepto, su importancia, cómo se aplica en la práctica profesional o académica, y si es pertinente, relaciónalo con otros conceptos del tema. "
        "Utiliza ejemplos, analogías, metáforas o comparaciones para facilitar la comprensión, pero sin perder el tono formal ni la profundidad académica.\n"
        "- Revisa los antecedentes del documento:\n{contexto_previos}\n"
        "- Incluye elementos valiosos de estos snippets web:\n{context_web}\n"
        "- No repitas ni copies literalmente conceptos ya generados en otros temas:\n{conceptos_previos}\n"
        "\n"
        "Entrega únicamente la lista de los siete conceptos, con su explicación de párrafo extenso cada uno, sin títulos adicionales ni instrucciones. "
        "El formato debe ser:\n"
        "**Concepto 1:** Párrafo explicativo de al menos 6 líneas.\n\n"
        "**Concepto 2:** Párrafo explicativo de al menos 6 líneas.\n\n"
        "...(continúa hasta 7 conceptos)..."
    )
)

conceptos_clave_chain = LLMChain(llm=llm, prompt=conceptos_clave_prompt_template)

def main():
    print("--- Ejecutando Agente7ConceptosClave por tema ---")
    contexto_global = leer_contexto_global()
    previos_texto = "\n".join([
        f"Resumen de '{k}':\n{(v[:350]+'...' if isinstance(v,str) else json.dumps(v)[:350]+'...' if v else 'Sin contenido.')}"
        for k, v in contexto_global.items()
    ]) or "No hay antecedentes de secciones previas."
    if not previos_texto:
        previos_texto = "No hay antecedentes de secciones previas."

    materia = fetch_course_data()
    if not materia:
        print("Agente7ConceptosClave: No se encontró información de la materia. Terminando.")
        sys.stdout.write("Error: No se pudo obtener la información del curso.")
        return

    nombre_curso = materia.get("Nombre del Programa", "Curso Desconocido")
    nivel_estudios = materia.get("Nivel de Estudios", "Nivel Desconocido")
    temas = materia.get("Entrega Contenidos", [])
    if not temas:
        print("No hay temas en 'Entrega Contenidos'.")
        sys.exit(1)

    resultados = []
    conceptos_previos_todos = ""  # Acumulador para que evite repeticiones

    for idx, tema in enumerate(temas):
        tema = tema.strip()
        search_query = f"definiciones conceptos clave fundamentales {tema} en {nombre_curso} para {nivel_estudios}"
        print(f"\nAgente7ConceptosClave: Buscando en la web para el tema '{tema}'...")
        serper_data = search_web_serper(search_query, limit_organic=4)
        context_web = get_best_snippets(serper_data, limit=4)
        if not context_web:
            context_web = "No se encontró información adicional en la web para los conceptos clave."

        print(f"Agente7ConceptosClave: Generando conceptos clave para el tema '{tema}'...")
        try:
            conceptos_contenido = conceptos_clave_chain.invoke({
                "nombre_curso": nombre_curso,
                "nivel_estudios": nivel_estudios,
                "tema": tema,
                "context_web": context_web,
                "contexto_previos": previos_texto,
                "conceptos_previos": conceptos_previos_todos[-1800:]  # Solo un extracto de los previos para el prompt
            })
            if hasattr(conceptos_contenido, "content"):
                conceptos_contenido = conceptos_contenido.content
            elif isinstance(conceptos_contenido, dict) and "text" in conceptos_contenido:
                conceptos_contenido = conceptos_contenido["text"]

            resultados.append({
                "tema": tema,
                "conceptos_clave": conceptos_contenido
            })
            conceptos_previos_todos += "\n\n" + conceptos_contenido  # Se los pasa a los siguientes temas para evitar repeticiones

        except Exception as e:
            print(f"Error al generar conceptos para el tema '{tema}': {e}")

    with open("agente7ConceptosClave.json", "w", encoding="utf-8") as f:
        json.dump(resultados, f, ensure_ascii=False, indent=2)

    print("\n--- Agente7ConceptosClave finalizado. Contenido guardado en 'agente7ConceptosClave.json' ---")


if __name__ == "__main__":
    main()

