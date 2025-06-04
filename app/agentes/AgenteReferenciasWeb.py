import os
import requests
import json
import sys

from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from langchain.chains import LLMChain

# ... tus claves/configuración ...
GROQ_API_KEY = "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"
SERPER_API_KEY = "5f7dbe7e7ce70029c6cddd738417a3e4132d6e47"

llm = ChatGroq(
    model_name="llama3-70b-8192", 
    api_key=GROQ_API_KEY,
    temperature=0.3,
    max_tokens=2200
)

def search_web_serper(query, limit_organic=5):
    url = "https://google.serper.dev/search"
    headers = {"X-API-KEY": SERPER_API_KEY, "Content-Type": "application/json"}
    data = {"q": query}
    try:
        response = requests.post(url, headers=headers, json=data, timeout=15)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error en Serper: {e}")
    return {"error": "No se pudo buscar"}

def get_best_snippets(serper_response, limit=5):
    if not serper_response or "organic" not in serper_response:
        return ""
    snippets = [r.get("snippet", "") for r in serper_response["organic"] if r.get("snippet")]
    return "\n".join(snippets[:limit])

def get_result_links(serper_response, limit=10):
    if not serper_response or "organic" not in serper_response:
        return []
    return [r.get("link") for r in serper_response["organic"][:limit] if r.get("link")]

referencias_prompt_template = PromptTemplate(
    input_variables=["pregunta", "context_web"],
    template=(
        "Usa la siguiente información encontrada en la web como contexto para responder la pregunta:\n"
        "{context_web}\n\n"
        "Pregunta: {pregunta}\n\n"
        "Proporciona una respuesta clara y breve. Al final, incluye la sección 'Referencias web utilizadas' con todos los links originales consultados (uno por línea, formato: - https://... )"
    )
)
referencias_chain = LLMChain(llm=llm, prompt=referencias_prompt_template)

def obtener_referencia_para_pregunta(pregunta):
    serper_data = search_web_serper(pregunta, limit_organic=6)
    context_web = get_best_snippets(serper_data, limit=4)
    links = get_result_links(serper_data, limit=6)
    links_text = "\n".join(f"- {l}" for l in links if l)

    try:
        respuesta = referencias_chain.invoke({
            "pregunta": pregunta,
            "context_web": context_web
        })
        if hasattr(respuesta, "content"):
            respuesta = respuesta.content
        elif isinstance(respuesta, dict) and "text" in respuesta:
            respuesta = respuesta["text"]
        if "Referencias web utilizadas" not in respuesta:
            respuesta += "\n\nReferencias web utilizadas:\n" + links_text
        return {
            "pregunta": pregunta,
            "respuesta": respuesta,
            "referencias": links  # por si quieres usarlas aparte
        }
    except Exception as e:
        print(f"Error en AgenteReferenciasWeb: {e}")
        return {
            "pregunta": pregunta,
            "respuesta": "",
            "referencias": []
        }

def main():
    # Puedes tener un listado de preguntas aquí:
    preguntas = [
        "¿Cuáles son los fundamentos del aprendizaje activo en educación superior?",
        # Puedes agregar más preguntas aquí
    ]
    resultados = []

    for pregunta in preguntas:
        print(f"\nProcesando pregunta: {pregunta}\n")
        resultado = obtener_referencia_para_pregunta(pregunta)
        resultados.append(resultado)

    # Al final guarda TODO en un solo archivo JSON
    with open("agenteReferenciasWeb.json", "w", encoding="utf-8") as f:
        json.dump(resultados, f, ensure_ascii=False, indent=2)
    print("Todos los resultados se guardaron en 'agenteReferenciasWeb.json'.")

if __name__ == "__main__":
    main()
