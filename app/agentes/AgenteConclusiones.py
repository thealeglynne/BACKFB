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

# ===============================
# LLM Configuration
llm = ChatGroq(
    model_name="llama3-70b-8192",
    api_key=GROQ_API_KEY,
    temperature=0.4,
    max_tokens=1800
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
    snippets = [r.get("snippet", "") for r in serper_response.get("organic", []) if r.get("snippet")]
    return "\n".join(snippets[:limit])

# === PROMPT DEL AGENTE ===
conclusiones_prompt_template = PromptTemplate(
    input_variables=["nombre_curso", "expert_name", "context_web", "contexto_previos"],
    template=(
        "Actúa como guionista de cierre académico para una unidad de '{nombre_curso}'. "
        "Elabora un diálogo entre Presentador y el/la experto/a '{expert_name}'. "
        "Incluye referencias a los antecedentes del documento:\n{contexto_previos}\nY contexto web:\n{context_web}\n"
        "\n"
        "Estructura:\n"
        "- Presentador da la bienvenida y contextualiza el cierre.\n"
        "- Presentador solicita a {expert_name} un resumen de los aprendizajes clave, vinculando cada tema a competencias y situaciones profesionales.\n"
        "- {expert_name} responde desarrollando los puntos principales, explicando cómo estos conocimientos impactan la formación integral y el futuro del estudiante.\n"
        "- {expert_name} ofrece una reflexión motivadora sobre la importancia de la formación continua.\n"
        "- Presentador despide agradeciendo y motivando a los estudiantes.\n"
        "Mantén un tono formal, reflexivo, y de cierre editorial. Incluye transiciones suaves y frases de inspiración final."
    )
)

conclusiones_chain = LLMChain(llm=llm, prompt=conclusiones_prompt_template)

def main():
    print("--- Ejecutando AgenteConclusiones ---")
    contexto_global = leer_contexto_global()
    previos_texto = "\n".join([
        f"Resumen de '{k}':\n{(v[:350]+'...' if isinstance(v, str) else json.dumps(v)[:350]+'...' if v else 'Sin contenido.')}"
        for k, v in contexto_global.items()
    ]) or "No hay resumen disponible de las secciones previas."

    materia = fetch_course_data()
    if not materia:
        print("AgenteConclusiones: No se encontró información de la materia. Terminando.")
        sys.stdout.write("Error: No se pudo obtener la información del curso.")
        return

    nombre_curso = materia.get("Nombre del Programa", "Curso Desconocido")
    expert_name = f"el/la Profesor(a) especialista en {nombre_curso}"

    search_query = f"importancia futura y conclusiones clave de {nombre_curso} en el ámbito profesional"
    print(f"AgenteConclusiones: Buscando en la web con query: '{search_query}'")
    serper_data = search_web_serper(search_query, limit_organic=3)
    context_web = get_best_snippets(serper_data, limit=3)
    if not context_web:
        context_web = f"No se encontró información web adicional sobre el futuro de {nombre_curso}."
        print("AgenteConclusiones: No se obtuvieron snippets de la búsqueda web.")

    print("AgenteConclusiones: Generando contenido...")
    try:
        conclusiones_contenido = conclusiones_chain.invoke({
            "nombre_curso": nombre_curso,
            "expert_name": expert_name,
            "context_web": context_web,
            "contexto_previos": previos_texto
        })
        if isinstance(conclusiones_contenido, dict) and "text" in conclusiones_contenido:
            conclusiones_contenido = conclusiones_contenido["text"]
        sys.stdout.write(conclusiones_contenido)
        print("\n--- AgenteConclusiones finalizado ---")
    except Exception as e:
        error_msg = f"Error en AgenteConclusiones al generar contenido: {str(e)}"
        print(error_msg)
        sys.stdout.write(f"Error interno en AgenteConclusiones: No se pudieron generar las conclusiones para {nombre_curso}.")

if __name__ == "__main__":
    main()
