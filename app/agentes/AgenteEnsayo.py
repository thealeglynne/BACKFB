from config import GROQ_API_KEY, SERPER_API_KEY, JSON_BIN_ID, JSON_BIN_API_KEY, CONTEXTO_GLOBAL_FILE
import os
import requests
import json
import sys
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from langchain.chains import LLMChain

# LLM Configuration
llm = ChatGroq(
    model_name="llama3-70b-8192",
    api_key=GROQ_API_KEY,
    temperature=0.5,
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
    except requests.exceptions.Timeout:
        print(f"Error: Timeout al intentar acceder a JSON Bin ({url}).")
    except requests.exceptions.RequestException as e:
        print(f"Error de red al acceder a JSON Bin: {e}")
    except json.JSONDecodeError:
        print(f"Error al decodificar JSON de la respuesta del bin: {res.text if 'res' in locals() else 'No response'}")
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
    except requests.exceptions.Timeout:
        print(f"Error: Timeout en la búsqueda web con Serper para query: {query}")
    except requests.exceptions.RequestException as e:
        print(f"Error de red en la búsqueda web con Serper: {e}")
    except json.JSONDecodeError:
        print(f"Error al decodificar JSON de la respuesta de Serper: {response.text if 'response' in locals() else 'No response'}")
    return {"error": "No se pudo realizar la búsqueda"}

def get_best_snippets(serper_response, limit=5):
    if not serper_response or "error" in serper_response or "organic" not in serper_response:
        return ""
    snippets = [r.get("snippet", "") for r in serper_response["organic"] if r.get("snippet")]
    return "\n".join(snippets[:limit])

# === PROMPT DEL AGENTE ===
ensayo_podcast_prompt_template = PromptTemplate(
    input_variables=["nombre_curso", "essay_topic", "context_web", "contexto_previos"],
    template=(
        "Actúa como guionista académico institucional para un podcast universitario. "
        "Tu guion debe explorar el tema '{essay_topic}' dentro de la unidad '{nombre_curso}' con profundidad conceptual y claridad narrativa.\n"
        "Revisa estos antecedentes:\n{contexto_previos}\nY el contexto web:\n{context_web}\n"
        "\n"
        "Estructura obligatoria (sin títulos extra):\n"
        "1. Título del segmento.\n"
        "2. [Introducción del Host]: Breve bienvenida, explicación del propósito y motivación inicial.\n"
        "3. [Enganche Inicial]: Dato curioso, pregunta potente o anécdota histórica relevante.\n"
        "4. [Desarrollo]: Expone el tema en varios párrafos, conecta hitos históricos, evolución conceptual, impacto actual, desafíos y proyecciones. Relaciona el contenido con competencias profesionales reales, incluye ejemplos o analogías, y utiliza transiciones fluidas.\n"
        "5. [Recomendación]: Sugerencia de libro, artículo, video o recurso serio y real, con justificación breve.\n"
        "6. [Conclusión]: Recapitula lo esencial, motiva al oyente a profundizar, invita a la acción o a la siguiente entrega.\n"
        "Cuida la coherencia y la calidad del lenguaje, integra frases de transición y reflexión."
    )
)

ensayo_podcast_chain = LLMChain(llm=llm, prompt=ensayo_podcast_prompt_template)

def main():
    print("--- Ejecutando AgenteEnsayo ---")
    contexto_global = leer_contexto_global()
    previos_texto = "\n".join([f"Contenido de '{k}':\n{v}\n" for k, v in contexto_global.items()])
    if not previos_texto:
        previos_texto = "No hay antecedentes de secciones previas."

    materia = fetch_course_data()
    if not materia:
        print("AgenteEnsayo: No se encontró información de la materia. Terminando.")
        sys.stdout.write("Error: No se pudo obtener la información del curso.")
        return

    nombre_curso = materia.get("Nombre del Programa", "Curso Desconocido")
    
    essay_topic = f"La Historia, Evolución e Impacto de {nombre_curso}"

    search_query = f"historia evolución impacto de {nombre_curso} tendencias futuras"
    print(f"AgenteEnsayo: Buscando en la web con query: '{search_query}'")
    serper_data = search_web_serper(search_query, limit_organic=6)
    context_web = get_best_snippets(serper_data, limit=6)
    if not context_web:
        context_web = f"No se encontró información web detallada sobre {essay_topic}."
        print("AgenteEnsayo: No se obtuvieron snippets de la búsqueda web.")

    print("AgenteEnsayo: Generando contenido...")
    try:
        ensayo_contenido = ensayo_podcast_chain.run(
            nombre_curso=nombre_curso,
            essay_topic=essay_topic,
            context_web=context_web,
            contexto_previos=previos_texto
        )
        sys.stdout.write(ensayo_contenido)
        print("\n--- AgenteEnsayo finalizado ---")
    except Exception as e:
        error_msg = f"Error en AgenteEnsayo al generar contenido: {str(e)}"
        print(error_msg)
        sys.stdout.write(f"Error interno en AgenteEnsayo: No se pudo generar el ensayo/podcast para {nombre_curso}.")

if __name__ == "__main__":
    main()
