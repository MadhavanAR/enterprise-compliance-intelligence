# Document ingestion module
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pathlib import Path
from rag.store import store_chunks

def load_and_chunk():
    file_path = Path("data/sample_doc.txt")
    text = file_path.read_text()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=600,
        chunk_overlap=100
    )

    chunks = splitter.split_text(text)

    print(f"Total chunks created: {len(chunks)}")
    for i, chunk in enumerate(chunks):
        print(f"\n--- Chunk {i} ---\n{chunk[:200]}")

    return chunks   # ✅ IMPORTANT

if __name__ == "__main__":
    chunks = load_and_chunk()
    store_chunks(chunks)
    print("Stored chunks in Qdrant")