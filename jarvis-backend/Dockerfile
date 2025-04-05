FROM python:3.10-slim

WORKDIR /app

# Copia os arquivos da pasta jarvis-backend para dentro do container
COPY . .

# Instala as dependências
RUN pip install --no-cache-dir -r requirements.txt

# Expõe a API com Uvicorn na porta 5000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5000"]

