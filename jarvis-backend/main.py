from fastapi import FastAPI, Request
from rag_engine import get_retriever
from langchain.chains import RetrievalQA
from langchain.llms import Ollama

app = FastAPI()

retriever = get_retriever()
llm = Ollama(model="phi", base_url="http://ollama:11434")
qa = RetrievalQA.from_chain_type(llm=llm, retriever=retriever)

@app.post("/ask")
async def ask(request: Request):
    body = await request.json()
    question = body.get("question", "")
    if not question:
        return {"error": "Pergunta não encontrada no corpo da requisição."}
    answer = qa.run(question)
    return {"answer": answer}

