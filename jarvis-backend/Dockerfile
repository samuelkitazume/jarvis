FROM python:3.10

WORKDIR /app

# Copia os arquivos da pasta jarvis-backend para dentro do container
COPY . .

# Atualiza pip, setuptools e wheel
RUN pip install --upgrade pip setuptools wheel

# Instala as dependências
RUN pip install --no-cache-dir -r requirements.txt

# Expõe a API com Uvicorn na porta 5000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5000"]

