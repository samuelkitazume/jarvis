# main.py
import os
import yaml
from fastapi import FastAPI, Request
from dotenv import load_dotenv

# LangChain Community (OpenAPI Agent)
from langchain_community.agent_toolkits.openapi.base import create_openapi_agent, OpenAPIToolkit
from langchain_community.agent_toolkits.openapi.toolkit import OpenAPIToolkit
from langchain_community.utilities.requests import TextRequestsWrapper
from langchain_community.tools.json.tool import JsonSpec


# LLM local (Ollama)
from langchain_ollama import OllamaLLM

# para debugar
import requests

# Carrega variáveis de ambiente do .env
load_dotenv()
bearer_token = os.getenv("API_TOKEN")

# Headers personalizados, como o token de autenticação do Home Assistant
custom_headers = {
    "Authorization": f"Bearer {bearer_token}",
    "Content-Type": "application/json"
}

# DEBUG: Testa conexão com um IP específico
print(">>>>>>>>> debugging with request", flush=True)
try:
    debug_ip = "http://192.168.2.72:8123/api/"  # substitua pelo IP real do seu servidor
    debug_response = requests.get(debug_ip, headers=custom_headers, timeout=3)
    print(f"DEBUG: Conexão bem-sucedida com {debug_ip} - Status: {debug_response.status_code}", flush=True)
except Exception as debug_error:
    print(f"DEBUG: Falha ao conectar com {debug_ip} - Erro: {debug_error}", flush=True)

app = FastAPI()

# 1. Lê seu arquivo YAML local (ex: home_assistant.yaml)
with open("home_assistant.yaml", "r") as f:
    raw_spec = yaml.safe_load(f)

# 2. Cria o objeto OpenAPISpec
json_spec = JsonSpec.parse_obj({"dict_": raw_spec})

# Cria o requests wrapper com os headers
requests_wrapper = TextRequestsWrapper(headers=custom_headers)

# 4. Cria o LLM local (Ollama, rodando phi, etc.)
llm = OllamaLLM(model="phi", base_url="http://ollama:11434")

toolkit = OpenAPIToolkit.from_llm(
    llm=llm,
    json_spec=json_spec,
    requests_wrapper=requests_wrapper,
    allow_dangerous_requests=True  # se quiser permitir chamadas sem confirmação
)
# 6. Gera o agente OpenAPI (ele decide qual endpoint usar)
agent = create_openapi_agent(llm=llm, toolkit=toolkit, verbose=True)

def should_use_agent(question: str) -> bool:
    intent_prompt = f"""
    Question from the user: {question}

    Would this question require a consultation to his Home Assistant REST API for a more accurate answer?

    Answer me with only one word: 'yes' or 'no'
    """
    result = llm.invoke(intent_prompt)
    print(f"[ROUTER PROMPT] {intent_prompt}", flush=True)
    print(f"[SHOULD USE AGENT RESPONSE] {result}", flush=True)
    return "yes" in result.lower()

def generate_fallback_response(question: str, error: str) -> str:
    fallback_prompt = f"""
Something went wrong when requesting Home Assistant API to answer the following question:

"{question}"

Erro: {error}

Generate a brief and friendly response explaining this to the user
"""
    return llm.invoke(fallback_prompt)

@app.post("/ask")
async def ask(request: Request):
    body = await request.json()
    question = body.get("question")
    if not question:
        return {"error": "Pergunta não encontrada"}

    if should_use_agent(question):
        try:
            answer = await agent.run(question)
            return {"answer": answer}
        except Exception as e:
            return generate_fallback_response(question, e)
    else:
        return llm.invoke(question)
