
import os
from langchain.document_loaders import DirectoryLoader, PyPDFLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import Chroma

# === CONFIGURAZIONI ===
DOCS_DIR = "data/docs"
CHROMA_DIR = "data/chroma_db"

# Collezioni separate
COLLECTIONS = {
    "informazioni_aziendali.pdf": "azienda_docs",
    "linee_guida.pdf": "relazione_docs",
}

def ingest_single_pdf(pdf_path, collection_name, embeddings):
    print("\n Indicizzazione di: {pdf_path} → collezione '{collection_name}'")

    # Carica documento
    loader = PyPDFLoader(pdf_path)
    docs = loader.load()

    # Split in chunk
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
    chunks = splitter.split_documents(docs)

    # Crea / aggiorna il database Chroma
    vectordb = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=CHROMA_DIR,
        collection_name=collection_name
    )
    vectordb.persist()
    print(f"Salvato {len(chunks)} chunk nella collezione '{collection_name}'")

def main():
    # Carica modello embeddings
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

    # Cicla su ogni documento definito
    for filename, collection_name in COLLECTIONS.items():
        pdf_path = os.path.join(DOCS_DIR, filename)
        if not os.path.exists(pdf_path):
            print(f"File mancante: {pdf_path}")
            continue
        ingest_single_pdf(pdf_path, collection_name, embeddings)

    print("\nIndicizzazione completata!")

if __name__ == "__main__":
    os.makedirs(DOCS_DIR, exist_ok=True)
    os.makedirs(CHROMA_DIR, exist_ok=True)
    main()