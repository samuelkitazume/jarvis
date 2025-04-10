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

# Carrega variáveis de ambiente do .env
load_dotenv()
bearer_token = os.getenv("API_TOKEN")

app = FastAPI()

# 1. Lê seu arquivo YAML local (ex: home_assistant.yaml)
with open("home_assistant.yaml", "r") as f:
    raw_spec = yaml.safe_load(f)

# 2. Cria o objeto OpenAPISpec
json_spec = JsonSpec.parse_obj({"dict_": raw_spec})

# Headers personalizados, como o token de autenticação do Home Assistant
custom_headers = {
    "Authorization": f"Bearer {bearer_token}",
    "Content-Type": "application/json"
}

# Cria o requests wrapper com os headers
requests_wrapper = TextRequestsWrapper(headers=custom_headers)

# 4. Cria o LLM local (Ollama, rodando phi, etc.)
llm = OllamaLLM(model="phi", base_url="http://localhost:11434")


toolkit = OpenAPIToolkit.from_llm(
    llm=llm,
    json_spec=json_spec,
    requests_wrapper=requests_wrapper,
    allow_dangerous_requests=True  # se quiser permitir chamadas sem confirmação
)
# 6. Gera o agente OpenAPI (ele decide qual endpoint usar)
agent = create_openapi_agent(llm=llm, toolkit=toolkit, verbose=True)

@app.post("/ask")
async def ask(request: Request):
    body = await request.json()
    question = body.get("question")
    if not question:
        return {"error": "Pergunta não encontrada"}

    try:
        # 7. Executa a chain do agente
        answer = await agent.run(question)
        return {"answer": answer}
    except Exception as e:
        return {"error": str(e)}