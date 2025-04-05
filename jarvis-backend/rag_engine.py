from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_community.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
import os

CHROMA_DIR = "/chroma"
DATA_FILE = "data/smart_home.txt"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"


def index_documents():
    if not os.path.exists(DATA_FILE):
        raise FileNotFoundError(f"Arquivo de dados não encontrado: {DATA_FILE}")

    loader = TextLoader(DATA_FILE, encoding="utf-8")
    docs = loader.load()

    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = splitter.split_documents(docs)

    embeddings = SentenceTransformerEmbeddings(model_name=EMBEDDING_MODEL)
    db = Chroma.from_documents(chunks, embedding=embeddings, persist_directory=CHROMA_DIR)
    print("Indexação concluída com sucesso.")


def get_retriever():
    embeddings = SentenceTransformerEmbeddings(model_name=EMBEDDING_MODEL)
    return Chroma(persist_directory=CHROMA_DIR, embedding_function=embeddings).as_retriever()

