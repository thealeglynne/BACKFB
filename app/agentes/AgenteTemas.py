import os
import requests
import json
import sys
from langchain_groq import ChatGroq

# ==============================
# CONFIGURACIÓN DE CLAVES Y CONSTANTES

GROQ_API_KEY = "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"
SERPER_API_KEY = "5f7dbe7e7ce70029c6cddd738417a3e4132d6e47"
JSON_BIN_ID = "682f27e08960c979a59f5afe"
JSON_BIN_API_KEY = "$2a$10$CWeZ66JKpedXMgIy/CDyYeEoH18x8tgxZDNBGDeHRSAusOVtHrwce"
CONTEXTO_GLOBAL_FILE = "contexto_global.json"

# ==============================
# INICIALIZA EL LLM (Modelo de lenguaje)
llm = ChatGroq(
    model_name="llama3-70b-8192",
    api_key=GROQ_API_KEY,
    temperature=0.4,
    max_tokens=3000
)

# ==============================
# FUNCIONES ÚTILES

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
            # Manejo flexible si no viene con 'record'
            if isinstance(data, dict) and "Nombre del Programa" in data:
                record = data
            elif isinstance(data, list) and data:
                record = data[-1]
                if not isinstance(record, dict):
                    print(f"Advertencia: El último elemento del JSON Bin no es un diccionario: {record}")
                    return None
            else:
                print(f"Error: La respuesta del JSON Bin no contiene 'record' ni es el registro directamente. Respuesta: {data}")
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

def update_course_data(new_data):
    """Sobrescribe el contenido del BIN (CUIDADO: reemplaza todo el JSON)"""
    url = f"https://api.jsonbin.io/v3/b/{JSON_BIN_ID}"
    headers = {
        "Content-Type": "application/json",
        "X-Master-Key": JSON_BIN_API_KEY
    }
    try:
        res = requests.put(url, headers=headers, json=new_data, timeout=10)
        res.raise_for_status()
        return res.json()
    except requests.exceptions.Timeout:
        print(f"Error: Timeout al intentar actualizar JSON Bin ({url}).")
    except requests.exceptions.RequestException as e:
        print(f"Error de red al actualizar JSON Bin: {e}")
    except Exception as e:
        print(f"Error inesperado al actualizar datos en JSON Bin: {e}")
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

# ==============================
# PRUEBA Y DEMO DE USO

if __name__ == "__main__":
    print("\n===== LEYENDO BIN =====\n")
    datos = fetch_course_data()
    print("Datos actuales en el bin:\n", json.dumps(datos, indent=2, ensure_ascii=False))

    print("\n===== ACTUALIZANDO BIN =====\n")
    if datos:
        datos["campo_actualizado"] = "Nuevo valor de prueba"  # Ejemplo de cambio
        resultado = update_course_data(datos)
        print("Respuesta de actualización:", resultado)
    else:
        print("No hay datos para actualizar.")

    print("\n===== BUSCANDO SNIPPETS WEB =====\n")
    resultados_web = search_web_serper("inteligencia artificial en educación", limit_organic=3)
    print("Snippets web:\n", get_best_snippets(resultados_web, limit=3))

    print("\n===== LLM INICIALIZADO =====\n")
    print(llm)
