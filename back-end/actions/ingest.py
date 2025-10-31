
import os
from langchain.document_loaders import DirectoryLoader, PyPDFLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import Chroma

# Directory dei documenti e del DB locale
DOCS_DIR = "data/docs"
CHROMA_DIR = "data/chroma_db"

# Carica documenti PDF e TXT
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

    # Chunking
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
    chunks = splitter.split_documents(docs)
    print(f"Creati {len(chunks)} chunk")

    # Embeddings locali HuggingFace
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

    # Salva su Chroma
    vectordb = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=CHROMA_DIR,
        collection_name="company_docs"
    )
    vectordb.persist()
    print(f"DB Chroma salvato in {CHROMA_DIR}")

if __name__ == "__main__":
    os.makedirs(DOCS_DIR, exist_ok=True)
    os.makedirs(CHROMA_DIR, exist_ok=True)
    main()