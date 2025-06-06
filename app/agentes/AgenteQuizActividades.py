import os
import requests
import json
import sys
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from langchain.chains import LLMChain

# === NUEVA FUNCIÓN FLEXIBLE DE EXTRACCIÓN ===
def get_value(materia, posibles_nombres, default=""):
    for name in posibles_nombres:
        if name in materia:
            return materia[name]
    # Variante por minúsculas y sin tildes
    for name in posibles_nombres:
        for k in materia:
            if k.lower().replace('í','i').replace('á','a').replace('é','e').replace('ó','o').replace('ú','u') == name.lower().replace('í','i').replace('á','a').replace('é','e').replace('ó','o').replace('ú','u'):
                return materia[k]
    return defaults

# Configuración de claves y constantes
GROQ_API_KEY = "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"
SERPER_API_KEY = "5f7dbe7e7ce70029c6cddd738417a3e4132d6e47"
JSON_BIN_ID = "682f27e08960c979a59f5afe"
JSON_BIN_API_KEY = "$2a$10$CWeZ66JKpedXMgIy/CDyYeEoH18x8tgxZDNBGDeHRSAusOVtHrwce"
CONTEXTO_GLOBAL_FILE = "contexto_global.json"

llm = ChatGroq(
    model_name="llama3-70b-8192",
    api_key=GROQ_API_KEY,
    temperature=0.3,
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
    except Exception:
        return {"error": "No se pudo realizar la búsqueda"}

def get_best_snippets(serper_response, limit=5):
    if not serper_response or "error" in serper_response or "organic" not in serper_response:
        return ""
    snippets = [r.get("snippet", "") for r in serper_response.get("organic", []) if r.get("snippet")]
    return "\n".join(snippets[:limit])

quiz_actividades_prompt_template = PromptTemplate(
    input_variables=["nombre_curso", "nivel", "tema", "contexto_previos", "context_web"],
    template=(
        "Actúa como diseñador académico universitario especializado en evaluación de aprendizajes. Vas a crear la sección de 'Actividades de evaluación y quiz' para el tema '{tema}' "
        "de la unidad '{nombre_curso}' (nivel: {nivel}), integrando los contenidos clave y competencias abordadas.\n\n"
        "Sigue estas INSTRUCCIONES ESTRICTAS:\n"
        "1. **Quiz de Selección Múltiple:** Elabora 5 preguntas de selección múltiple, cada una con:\n"
        "   - Enunciado claro y alineado con los contenidos fundamentales del tema\n"
        "   - 4 opciones de respuesta (a, b, c, d)\n"
        "   - Respuesta correcta marcada\n"
        "   - Una retroalimentación breve y académica para cada pregunta (que explique por qué la opción correcta es la más adecuada)\n"
        "   - Las preguntas deben abarcar todo el tema, evitar repeticiones y evaluar tanto conceptos como aplicación y análisis.\n"
        "2. **Quiz de Verdadero/Falso:** Formula 3 preguntas V/F, cada una con la respuesta correcta y una retroalimentación breve (que justifique la respuesta correcta). Incluye variedad conceptual y práctica.\n"
        "3. **Actividad Aplicada (opcional):** Propón una actividad breve de análisis o aplicación real, adecuada para estudiantes universitarios, alineada con el tema (ejemplo: un caso a resolver, una reflexión, o una mini-investigación). Incluye instrucciones claras.\n\n"
        "• Revisa e integra los antecedentes del documento:\n{contexto_previos}\n"
        "• Utiliza también este contexto web:\n{context_web}\n"
        "• Redacta de manera académica, clara, sin títulos ni bloques extra (entrega directo el contenido para copiar/pegar en el documento).\n"
        "• Garantiza que las preguntas y actividades sean variadas, relevantes y de nivel universitario. Evita repeticiones, ambigüedades o preguntas superficiales."
    )
)

quiz_actividades_chain = LLMChain(llm=llm, prompt=quiz_actividades_prompt_template)

def main():
    print("--- Ejecutando AgenteQuizActividades (por TEMA) ---")
    resultados = []

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

    # --------- CAMBIOS PARA FLEXIBILIDAD DE CAMPOS -----------
    nombre_curso = get_value(materia, ["Nombre de la Materia", "Nombre del Programa", "materia", "programa"], "Materia Desconocida")
    nivel = get_value(materia, ["Nivel de Estudios", "nivel", "Nivel"], "Nivel Desconocido")
    temas = get_value(materia, ["Entrega Contenidos", "temas", "contenidos"], [])
    if not temas:
        print("No hay temas en 'Entrega Contenidos'.")
        sys.exit(1)

    for tema in temas:
        tema = tema.strip()
        search_query = f"ejercicios actividades quiz evaluación {nombre_curso} {tema} nivel universitario"
        serper_data = search_web_serper(search_query, limit_organic=4)
        context_web = get_best_snippets(serper_data, limit=4)
        if not context_web:
            context_web = "No se encontró información adicional en la web para actividades y quiz."

        print(f"\n--- Generando actividades y quiz para el tema: {tema} ---")
        try:
            quiz_actividades_contenido = quiz_actividades_chain.invoke({
                "nombre_curso": nombre_curso,
                "nivel": nivel,
                "tema": tema,
                "contexto_previos": previos_texto,
                "context_web": context_web
            })
            if hasattr(quiz_actividades_contenido, "content"):
                quiz_actividades_contenido = quiz_actividades_contenido.content
            elif isinstance(quiz_actividades_contenido, dict) and "text" in quiz_actividades_contenido:
                quiz_actividades_contenido = quiz_actividades_contenido["text"]

            resultado = {
                "tema": tema,
                "actividades_y_quiz": quiz_actividades_contenido
            }
            resultados.append(resultado)
        except Exception as e:
            print(f"Error con tema {tema}: {e}")

    # Guarda todos los bloques en un único archivo JSON
    with open("agenteQuizActividades.json", "w", encoding="utf-8") as f:
        json.dump(resultados, f, ensure_ascii=False, indent=2)

    print("\n--- TODOS los temas se han guardado en 'agenteQuizActividades.json' ---")

if __name__ == "__main__":
    main()
