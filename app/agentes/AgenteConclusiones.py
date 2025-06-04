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
    input_variables=["nombre_curso", "tema", "expert_name", "context_web", "contexto_previos", "conclusion_previa"],
    template=(
        "Actúa como guionista de cierre académico para una unidad de '{nombre_curso}'. "
        "Elabora un diálogo de cierre creativo y reflexivo entre Presentador y el/la experto/a '{expert_name}', para el tema '{tema}'. "
        "Ya se hizo una conclusión previa para otro tema, así que esta vez usa un **enfoque diferente**, evita repetir frases, anécdotas o recursos, y elige otra forma de motivar y cerrar. "
        "Puedes incorporar frases célebres, metáforas, preguntas inspiradoras o recursos literarios que no se hayan usado en el anterior. "
        "Incluye referencias a los antecedentes del documento:\n{contexto_previos}\nY contexto web:\n{context_web}\n"
        "Puedes mencionar desafíos y oportunidades profesionales vinculados a este tema.\n"
        "Estructura:\n"
        "- Presentador da la bienvenida y contextualiza el cierre para el tema '{tema}'.\n"
        "- Presentador solicita a {expert_name} un resumen de los aprendizajes clave, vinculando cada tema a competencias y situaciones profesionales reales.\n"
        "- {expert_name} responde desarrollando los puntos principales, explicando cómo estos conocimientos impactan la formación integral y el futuro del estudiante, usando un recurso narrativo distinto al anterior.\n"
        "- {expert_name} ofrece una reflexión motivadora sobre la importancia de la formación continua, distinta a la previa.\n"
        "- Presentador despide agradeciendo y motivando a los estudiantes, con una frase final original.\n"
        "Mantén un tono formal, reflexivo y editorial, pero con toques originales y distintos en cada cierre. Usa transiciones suaves y frases de inspiración final."
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
