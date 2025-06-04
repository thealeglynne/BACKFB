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
        "Actúa como guionista académico institucional para un podcast universitario. "
        "Vas a crear un guion creativo, original y profesional sobre el tema '{essay_topic}' dentro de la unidad '{nombre_curso}'. "
        "Ya escribiste un ensayo anterior sobre '{ensayo_previo}'. En este nuevo ensayo, **NO repitas las mismas frases, ejemplos ni estilo**. "
        "Cambia la forma de enganchar, el tipo de ejemplos, analogías, o recursos narrativos. "
        "Usa metáforas, historias, analogías, citas célebres o recursos originales. Atrévete a variar el enfoque, pero siempre mantente dentro del rigor académico y del tema. "
        "Revisa estos antecedentes:\n{contexto_previos}\nY el contexto web:\n{context_web}\n"
        "\n"
        "Estructura obligatoria (sin títulos extra):\n"
        "1. Título del segmento.\n"
        "2. [Introducción del Host]: Breve bienvenida, explicación del propósito y motivación inicial.\n"
        "3. [Enganche Inicial]: Dato curioso, pregunta potente, cita o anécdota relevante distinta a la usada antes.\n"
        "4. [Desarrollo]: Expón el tema en varios párrafos, conecta hitos históricos, evolución conceptual, impacto actual, desafíos y proyecciones. Relaciona el contenido con competencias profesionales reales, incluye ejemplos o analogías, y utiliza transiciones fluidas.\n"
        "5. [Recomendación]: Sugerencia de libro, artículo, video o recurso serio y real, con justificación breve (diferente al anterior).\n"
        "6. [Conclusión]: Recapitula lo esencial, motiva al oyente a profundizar, invita a la acción o a la siguiente entrega."
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
