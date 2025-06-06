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
# LLM Configuration (sube la temperatura)
llm = ChatGroq(
    model_name="llama3-70b-8192",
    api_key=GROQ_API_KEY,
    temperature=0.85,    # ¡Para que haya más variedad y creatividad!
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

# === PROMPT DEL AGENTE (¡variado y diferente por tema!) ===
conclusiones_prompt_template = PromptTemplate(
    input_variables=["nombre_curso", "tema", "context_web", "contexto_previos", "conclusiones_previas"],
    template=(
        "Actúa como redactor académico universitario experto en elaboración de conclusiones para documentos extensos de formación profesional. "
        "Vas a escribir la sección de **Conclusiones** para el tema '{tema}' en la unidad del curso '{nombre_curso}'. "
        "La sección debe consistir en **cinco (5) conclusiones**, cada una desarrollada en un párrafo extenso de al menos 6 líneas. "
        "\n"
        "INSTRUCCIONES ESTRICTAS:\n"
        "- Cada conclusión debe integrar reflexiones profundas sobre todos los contenidos desarrollados en la unidad.\n"
        "- Relaciona la importancia de los conocimientos abordados, su aplicabilidad real en contextos profesionales y el impacto personal y ético del aprendizaje.\n"
        "- Aborda los desafíos, oportunidades y la relevancia de seguir actualizándose en el tema.\n"
        "- Cada conclusión debe aportar un ángulo diferente, evitando repeticiones y redundancias.\n"
        "- Evita frases genéricas o vacías: utiliza argumentación clara, ejemplos, referencias a situaciones reales, y reflexiones que motiven al estudiante a valorar y aplicar lo aprendido.\n"
        "- Utiliza tanto los antecedentes previos del documento como el contexto web proporcionado:\n{contexto_previos}\n{context_web}\n"
        "- Si existen conclusiones previas para otros temas, NO repitas ideas, argumentos ni recursos narrativos; busca originalidad en el enfoque y la redacción.\n"
        "- Mantén un tono formal, profundo, motivador y profesional. Redacta los cinco párrafos de corrido, sin títulos ni subtítulos.\n"
        "\n"
        "Entrega solo los 5 párrafos de conclusiones, cada uno claramente separado y extenso."
    )
)

conclusiones_chain = LLMChain(llm=llm, prompt=conclusiones_prompt_template)

def main():
    print("--- Ejecutando AgenteConclusiones (por tema) ---")
    resultados = []
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
    temas = materia.get("Entrega Contenidos", [])
    if not temas:
        print("No hay temas en 'Entrega Contenidos'.")
        sys.exit(1)

    conclusion_previa = ""
    for idx, tema in enumerate(temas):
        tema = tema.strip()
        search_query = f"importancia futura y conclusiones clave de {tema} en el ámbito profesional"
        print(f"\nAgenteConclusiones: Buscando en la web para el tema '{tema}' con query: '{search_query}'")
        serper_data = search_web_serper(search_query, limit_organic=3)
        context_web = get_best_snippets(serper_data, limit=3)
        if not context_web:
            context_web = f"No se encontró información web adicional sobre el futuro de {tema}."
            print(f"AgenteConclusiones: No se obtuvieron snippets de la búsqueda web para el tema '{tema}'.")

        print(f"AgenteConclusiones: Generando contenido para el tema '{tema}'...")
        try:
            conclusiones_contenido = conclusiones_chain.invoke({
                "nombre_curso": nombre_curso,
                "tema": tema,
                "expert_name": expert_name,
                "context_web": context_web,
                "contexto_previos": previos_texto,
                "conclusion_previa": conclusion_previa[:400] if conclusion_previa else "ninguna"
            })
            if hasattr(conclusiones_contenido, "content"):
                conclusiones_contenido = conclusiones_contenido.content
            elif isinstance(conclusiones_contenido, dict) and "text" in conclusiones_contenido:
                conclusiones_contenido = conclusiones_contenido["text"]

            resultado = {
                "tema": tema,
                "conclusion": conclusiones_contenido
            }
            resultados.append(resultado)
            conclusion_previa = conclusiones_contenido  # Así el siguiente tema será aún más distinto

        except Exception as e:
            print(f"Error al generar conclusión para el tema {tema}: {e}")

    # Guarda en un solo archivo JSON (uno por cada tema)
    with open("agenteConclusiones.json", "w", encoding="utf-8") as f:
        json.dump(resultados, f, ensure_ascii=False, indent=2)
    print("\n--- AgenteConclusiones finalizado. Contenido guardado en 'agenteConclusiones.json' ---")

if __name__ == "__main__":
    main()
