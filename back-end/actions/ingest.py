import os
from langchain.document_loaders import DirectoryLoader, PyPDFLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import Chroma

# === PERCORSI RELATIVI RISPETTO ALLA RADICE DEL PROGETTO ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # dove si trova ingest.py
DATA_DIR = os.path.join(BASE_DIR, "data/")
DOCS_DIR = os.path.join(DATA_DIR, "docs")
CHROMA_DIR = os.path.join(DATA_DIR, "chroma_db")
COLLECTION_NAME = "company_docs"

# === CREA CARTELLE SE NON ESISTONO ===
os.makedirs(DOCS_DIR, exist_ok=True)
os.makedirs(CHROMA_DIR, exist_ok=True)

# === CARICA DOCUMENTI ===
def load_documents():
    loaders = [
        DirectoryLoader(DOCS_DIR, glob="**/*.pdf", loader_cls=PyPDFLoader)
    ]
    docs = []
    for loader in loaders:
        try:
            docs.extend(loader.load())
        except Exception as e:
            print(f"Errore caricando {loader}: {e}")
    return docs

def main():
    docs = load_documents()
    print(f"Caricati {len(docs)} documenti")

    if not docs:
        print("Nessun documento trovato in data/docs")
        return

    splitter = RecursiveCharacterTextSplitter(chunk_size=1200, chunk_overlap=200)
    chunks = splitter.split_documents(docs)
    print(f"Creati {len(chunks)} chunk")

    # Embeddings locali multilingua
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
    )

    # Creazione database Chroma persistente
    vectordb = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=CHROMA_DIR,
        collection_name=COLLECTION_NAME
    )

    vectordb.persist()
    vectordb = None

    print(f"DB Chroma salvato in: {os.path.abspath(CHROMA_DIR)}")

if __name__ == "__main__":
    main()
