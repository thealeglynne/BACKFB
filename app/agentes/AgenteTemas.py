import os
import re
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

def safe_filename(text):
    return re.sub(r'[^a-zA-Z0-9_]', '', text.replace(" ", "_").lower())

def generar_contenido_tema(contexto):
    prompt = (
        f"Genera un documento académico completo para el tema '{contexto['tema']}' "
        f"dentro de la materia '{contexto['materia']}' de la carrera '{contexto['carrera']}', "
        f"semestre {contexto['semestre']}. "
        "La estructura debe incluir: Introducción, conceptos clave, desarrollo del tema, actividades, conclusiones, y referencias. "
        "Usa un tono institucional, académico, claro y motivador."
    )
    response = llm.invoke(prompt)
    if hasattr(response, "content"):
        return response.content
    if isinstance(response, str):
        return response
    return str(response)

if __name__ == "__main__":
    print("\n===== LEYENDO BIN =====\n")
    materia = fetch_course_data()
    if not materia:
        print("No se pudo obtener la materia desde JSON Bin.")
        sys.exit(1)
    temas = materia.get("Entrega Contenidos", [])
    if not temas:
        print("No hay temas en 'Entrega Contenidos'.")
        sys.exit(1)

    # Info general de materia/carrera/semestre
    carrera = materia.get("Nombre del Programa", "")
    nombre_materia = materia.get("Nombre de la Materia", "")
    semestre = materia.get("Semestre", "")

    resultados_temas = []  # <-- Aquí acumulamos los resultados de todos los temas

    for tema in temas:
        tema = tema.strip()
        print(f"\n==============================================")
        print(f"== GENERANDO DOCUMENTO PARA EL TEMA: {tema}")
        print(f"==============================================")
        contexto = {
            "carrera": carrera,
            "materia": nombre_materia,
            "semestre": semestre,
            "tema": tema,
        }
        contenido_generado = generar_contenido_tema(contexto)
        print(contenido_generado)
        resultados_temas.append({
            "tema": tema,
            "contenido": contenido_generado
        })

    # Al final, guarda todo en un único JSON
    with open("agenteTemas.json", "w", encoding="utf-8") as f:
        json.dump(resultados_temas, f, ensure_ascii=False, indent=2)

    print("\nTodos los temas se han guardado en 'agenteTemas.json'")
