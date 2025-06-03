import os
import requests
import json
import sys
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from langchain.chains import LLMChain

# ===============================
# CONFIGURACIÓN DIRECTA DE LAS APIS Y CONSTANTES

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
    temperature=0.3,  # Menor creatividad, mayor precisión
    max_tokens=2200
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

# === PROMPT DEL AGENTE QUIZ Y ACTIVIDADES ===

quiz_actividades_prompt_template = PromptTemplate(
    input_variables=["nombre_curso", "nivel", "contexto_previos", "context_web"],
    template=(
        "Actúa como diseñador académico para educación universitaria. Tu misión es generar la sección de Evaluación y Actividades para la unidad '{nombre_curso}' "
        "(nivel: {nivel}), integrando los conceptos clave, temas vistos y competencias de la unidad.\n"
        "\n"
        "Estructura la salida en TRES BLOQUES:\n"
        "1. Actividades de Aplicación: Redacta 2 actividades prácticas o ejercicios de desarrollo para reforzar lo aprendido, incluyendo enunciado claro, instrucciones, y criterios de evaluación.\n"
        "2. Quiz de Repaso: Crea 4 preguntas tipo quiz, cada una con:\n"
        "   - Enunciado (pregunta clara)\n"
        "   - 4 opciones (a, b, c, d)\n"
        "   - Respuesta correcta marcada\n"
        "   - Explicación breve de la respuesta\n"
        "3. Desafío Abierto: Propón una situación o problema realista en el contexto profesional, que requiera integración de varios conceptos de la unidad. Incluye orientación sobre cómo abordarlo.\n"
        "\n"
        "Incluye referencias a los antecedentes del documento:\n{contexto_previos}\n"
        "Y snippets de contexto web:\n{context_web}\n"
        "Cuida la redacción académica, claridad, variedad temática y relación con el contexto profesional."
    )
)

quiz_actividades_chain = LLMChain(llm=llm, prompt=quiz_actividades_prompt_template)

def main():
    print("--- Ejecutando AgenteQuizActividades ---")
    contexto_global = leer_contexto_global()
    previos_texto = "\n".join([
        f"Resumen de '{k}':\n{(v[:350]+'...' if isinstance(v,str) else json.dumps(v)[:350]+'...' if v else 'Sin contenido.')}"
        for k, v in contexto_global.items()
    ]) or "No hay antecedentes de secciones previas."

    materia = fetch_course_data()
    if not materia:
        print("AgenteQuizActividades: No se encontró información de la materia. Terminando.")
        sys.stdout.write("Error: No se pudo obtener la información del curso.")
        return

    nombre_curso = materia.get("Nombre del Programa", "Curso Desconocido")
    nivel = materia.get("Nivel de Estudios", "Nivel Desconocido")

    search_query = f"ejercicios actividades quiz evaluación {nombre_curso} nivel universitario"
    serper_data = search_web_serper(search_query, limit_organic=4)
    context_web = get_best_snippets(serper_data, limit=4)
    if not context_web:
        context_web = "No se encontró información adicional en la web para actividades y quiz."

    print("AgenteQuizActividades: Generando contenido de actividades y quiz...")
    try:
        quiz_actividades_contenido = quiz_actividades_chain.invoke({
            "nombre_curso": nombre_curso,
            "nivel": nivel,
            "contexto_previos": previos_texto,
            "context_web": context_web
        })
        # Si la respuesta viene en dict (como {"text": ...}), extrae el texto
        if isinstance(quiz_actividades_contenido, dict) and "text" in quiz_actividades_contenido:
            quiz_actividades_contenido = quiz_actividades_contenido["text"]
        sys.stdout.write(quiz_actividades_contenido)
        print("\n--- AgenteQuizActividades finalizado ---")
    except Exception as e:
        error_msg = f"Error en AgenteQuizActividades al generar contenido: {str(e)}"
        print(error_msg)
        sys.stdout.write(f"Error interno en AgenteQuizActividades: No se pudieron generar actividades y quiz para {nombre_curso}.")

if __name__ == "__main__":
    main()
