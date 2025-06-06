import os
import requests
import json
import sys
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from langchain.chains import LLMChain

# ===============================
# CONFIGURACIÓN DIRECTA DE APIS Y CONSTANTES

GROQ_API_KEY = "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"
SERPER_API_KEY = "5f7dbe7e7ce70029c6cddd738417a3e4132d6e47"
JSON_BIN_ID = "682f27e08960c979a59f5afe"
JSON_BIN_API_KEY = "$2a$10$CWeZ66JKpedXMgIy/CDyYeEoH18x8tgxZDNBGDeHRSAusOVtHrwce"
CONTEXTO_GLOBAL_FILE = "contexto_global.json"

llm = ChatGroq(
    model_name="llama3-70b-8192",
    api_key=GROQ_API_KEY,
    temperature=0.85,    # <--- Más creatividad
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
    snippets = [r.get("snippet", "") for r in serper_response.get("organic", []) if r.get("snippet")]
    return "\n".join(snippets[:limit])

# PROMPT MODIFICADO para creatividad y variedad
ensayo_podcast_prompt_template = PromptTemplate(
    input_variables=["nombre_curso", "essay_topic", "context_web", "contexto_previos", "ensayo_previo"],
    template=(
        "Eres un redactor académico creativo y versátil, experto en la elaboración de ensayos universitarios de alto nivel. "
        "Redacta un **ensayo académico original, profundo y argumentado** sobre el tema '{essay_topic}', como parte del curso '{nombre_curso}'.\n\n"
        "PAUTAS ESTRICTAS PARA LOGRAR VARIEDAD EN CADA ENSAYO:\n"
        "• El texto debe tener **al menos 6 párrafos** extensos (más de 6 líneas cada uno) y bien cohesionados, evitando estructuras repetitivas o enumerativas.\n"
        "• Utiliza perspectivas teóricas diversas: en cada ensayo, selecciona nuevos enfoques, corrientes de pensamiento, modelos o teorías pertinentes al área. Cita explícitamente autores, preferiblemente diferentes en cada ensayo, incluyendo autores internacionales.\n"
        "• Aborda el tema desde ángulos o preguntas problematizadoras diferentes, enfocándote en dimensiones menos abordadas en ensayos previos, o proponiendo hipótesis, dilemas éticos, tendencias futuras o desafíos contemporáneos.\n"
        "• Integra ejemplos novedosos, estudios de caso recientes, comparaciones internacionales y datos actualizados del contexto global.\n"
        "• Relaciona siempre el contenido teórico con competencias, habilidades y aplicaciones en entornos profesionales diversos, evitando generalizaciones y lugares comunes.\n"
        "• NO repitas ideas, recursos, citas ni estructura ya presentes en el ensayo anterior (ensayo_previo): cambia el enfoque, los ejemplos y los argumentos para garantizar originalidad total.\n"
        "• Si encuentras antecedentes relevantes, utiliza esa información para profundizar, complementar o incluso cuestionar visiones anteriores:\n{contexto_previos}\n"
        "• Incorpora aportes, datos o tendencias encontrados en este contexto web:\n{context_web}\n"
        "• La redacción debe ser académica, clara, matizada y rigurosa, evitando títulos, subtítulos, viñetas o divisiones explícitas.\n"
        "\n"
        "ENTREGA SOLO EL ENSAYO FLUIDO, SIN INSTRUCCIONES NI FORMATO EXTRA."
    )
)
ensayo_podcast_chain = LLMChain(llm=llm, prompt=ensayo_podcast_prompt_template)

def main():
    print("--- Ejecutando AgenteEnsayo por tema ---")
    resultados = []
    contexto_global = leer_contexto_global()
    previos_texto = "\n".join([
        f"Resumen de '{k}':\n{(v[:350]+'...' if isinstance(v, str) else json.dumps(v)[:350]+'...' if v else 'Sin contenido.')}"
        for k, v in contexto_global.items()
    ]) or "No hay antecedentes de secciones previas."
    if not previos_texto:
        previos_texto = "No hay antecedentes de secciones previas."

    materia = fetch_course_data()
    if not materia:
        print("AgenteEnsayo: No se encontró información de la materia. Terminando.")
        sys.stdout.write("Error: No se pudo obtener la información del curso.")
        return

    nombre_curso = materia.get("Nombre del Programa", "Curso Desconocido")
    temas = materia.get("Entrega Contenidos", [])
    if not temas:
        print("No hay temas en 'Entrega Contenidos'.")
        sys.exit(1)

    ensayo_anterior = ""
    for idx, tema in enumerate(temas):
        tema = tema.strip()
        essay_topic = f"La Historia, Evolución e Impacto de {tema}"
        search_query = f"historia evolución impacto de {tema} tendencias futuras"
        print(f"\nAgenteEnsayo: Buscando en la web para el tema '{tema}' con query: '{search_query}'")
        serper_data = search_web_serper(search_query, limit_organic=6)
        context_web = get_best_snippets(serper_data, limit=6)
        if not context_web:
            context_web = f"No se encontró información web detallada sobre {essay_topic}."
            print(f"AgenteEnsayo: No se obtuvieron snippets de la búsqueda web para el tema '{tema}'.")

        print(f"AgenteEnsayo: Generando contenido para el tema '{tema}'...")
        try:
            ensayo_contenido = ensayo_podcast_chain.invoke({
                "nombre_curso": nombre_curso,
                "essay_topic": essay_topic,
                "context_web": context_web,
                "contexto_previos": previos_texto,
                "ensayo_previo": ensayo_anterior[:400] if ensayo_anterior else "ninguno"
            })
            if hasattr(ensayo_contenido, "content"):
                ensayo_contenido = ensayo_contenido.content
            elif isinstance(ensayo_contenido, dict) and "text" in ensayo_contenido:
                ensayo_contenido = ensayo_contenido["text"]
            resultado = {
                "tema": tema,
                "ensayo": ensayo_contenido
            }
            resultados.append(resultado)
            ensayo_anterior = ensayo_contenido  # Para que el siguiente se diferencie aún más
        except Exception as e:
            print(f"Error al generar ensayo para el tema {tema}: {e}")

    # Guarda en un solo archivo JSON (uno por cada tema)
    with open("agenteEnsayo.json", "w", encoding="utf-8") as f:
        json.dump(resultados, f, ensure_ascii=False, indent=2)
    print("\n--- AgenteEnsayo finalizado. Contenido guardado en 'agenteEnsayo.json' ---")

if __name__ == "__main__":
    main()
