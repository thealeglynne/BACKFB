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
    temperature=0.3,
    max_tokens=1500
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

introduccion_prompt_template = PromptTemplate(
    input_variables=["nombre", "nivel", "modalidad", "semestre", "tema", "context", "contexto_previos"],
    template=(
        "Actúa como un redactor académico experto en educación universitaria y diseño curricular institucional. "
        "Redacta la introducción para el tema '{tema}' dentro de la unidad '{nombre}', en el programa de {nivel}, modalidad {modalidad}, semestre {semestre}. "
        "Tienes acceso a antecedentes previos del documento:\n"
        "{contexto_previos}\n"
        "Y el siguiente contexto web:\n"
        "{context}\n"
        "\n"
        "La introducción debe:\n"
        "- Consistir en TRES PÁRRAFOS académicos, claros y motivadores.\n"
        "- El primer párrafo contextualiza el tema dentro del plan de estudios, resalta su relevancia profesional y social, y establece una conexión inicial con el futuro desempeño del estudiante.\n"
        "- El segundo párrafo detalla los subtemas o elementos clave del tema, indicando por qué cada uno es fundamental. Usa frases de transición y relaciones entre ellos.\n"
        "- El tercer párrafo explica cómo el aprendizaje de este tema fortalece tanto el perfil profesional como el personal del estudiante, incluye una frase inspiradora o de invitación al aprendizaje.\n"
        "Solicita al final una sección de OBJETIVOS DE APRENDIZAJE con la frase exacta: 'Al finalizar este tema, serás capaz de:', seguida de una lista de 3 a 5 objetivos claros, cada uno en una línea, numerados.\n"
        "Procura mantener un tono institucional, redacción impecable y conectores lógicos entre las ideas. No incluyas títulos adicionales, solo el texto.\n"
        "Formato:\n"
        "[Párrafo 1]\n\n[Párrafo 2]\n\n[Párrafo 3]\n\nAl finalizar este tema, serás capaz de:\n1. ...\n2. ...\n3. ...\n"
    )
)

introduccion_chain = LLMChain(llm=llm, prompt=introduccion_prompt_template)

def main():
    print("--- Ejecutando AgenteIntroduccion POR TEMA ---")
    resultados = []

    contexto_global = leer_contexto_global()
    previos_texto = "\n".join([
        f"Resumen de '{k}':\n{(v[:350]+'...' if isinstance(v,str) else json.dumps(v)[:350]+'...' if v else 'Sin contenido.')}"
        for k, v in contexto_global.items()
    ]) or "No hay antecedentes de secciones previas."
    if not previos_texto:
        previos_texto = "No hay antecedentes de secciones previas."

    materia = fetch_course_data()
    if not materia:
        print("AgenteIntroduccion: No se encontró información de la materia en el bin. Terminando.")
        sys.stdout.write("Error: No se pudo obtener la información del curso.")
        return

    nombre = materia.get("Nombre del Programa", "Nombre del Programa Desconocido")
    nivel = materia.get("Nivel de Estudios", "Nivel Desconocido")
    modalidad = materia.get("Modalidad", "Modalidad Desconocida")
    semestre = materia.get("Semestre", "Semestre Desconocido")
    escuela = materia.get("Escuela", "Escuela Desconocida")
    temas = materia.get("Entrega Contenidos", [])
    if not temas:
        print("No hay temas en 'Entrega Contenidos'.")
        sys.exit(1)

    for tema in temas:
        tema = tema.strip()
        search_query = f"introducción a {tema} en {nombre} importancia y objetivos {nivel} {modalidad} semestre {semestre} {escuela}"
        print(f"\nAgenteIntroduccion: Buscando en la web para el tema '{tema}' con query: '{search_query}'")
        serper_data = search_web_serper(search_query, limit_organic=4)
        context_web = get_best_snippets(serper_data, limit=4)
        if not context_web:
            context_web = "No se encontró información adicional en la web."
            print(f"AgenteIntroduccion: No se obtuvieron snippets web para el tema '{tema}'.")

        print(f"AgenteIntroduccion: Generando contenido para el tema '{tema}'...")
        try:
            introduccion_contenido = introduccion_chain.invoke({
                "nombre": nombre,
                "nivel": nivel,
                "modalidad": modalidad,
                "semestre": semestre,
                "tema": tema,
                "context": context_web,
                "contexto_previos": previos_texto
            })
            if hasattr(introduccion_contenido, "content"):
                introduccion_contenido = introduccion_contenido.content
            elif isinstance(introduccion_contenido, dict) and "text" in introduccion_contenido:
                introduccion_contenido = introduccion_contenido["text"]

            resultado = {
                "tema": tema,
                "introduccion": introduccion_contenido
            }
            resultados.append(resultado)
        except Exception as e:
            print(f"Error al generar introducción para el tema {tema}: {e}")

    # Guarda en un solo archivo JSON (uno por cada tema)
    with open("agenteIntroduccion.json", "w", encoding="utf-8") as f:
        json.dump(resultados, f, ensure_ascii=False, indent=2)
    print("\n--- AgenteIntroduccion finalizado. Contenido guardado en 'agenteIntroduccion.json' ---")

if __name__ == "__main__":
    main()
