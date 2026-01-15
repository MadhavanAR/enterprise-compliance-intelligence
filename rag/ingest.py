# Document ingestion module
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pathlib import Path

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

if __name__ == "__main__":
    load_and_chunk()