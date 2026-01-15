from pathlib import Path
from langchain_text_splitters import RecursiveCharacterTextSplitter
from rag.store import store_chunks
from rag.logger import logger


def load_and_chunk(file_path: str = "data/sample_doc.txt") -> list[str]:
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"Data file not found: {file_path}")

    text = path.read_text()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=600,
        chunk_overlap=100
    )

    chunks = splitter.split_text(text)

    logger.info(f"Total chunks created: {len(chunks)}")

    for i, chunk in enumerate(chunks):
        logger.debug(f"Chunk {i}: {chunk[:200]}")

    return chunks


def main():
    chunks = load_and_chunk()
    store_chunks(chunks)
    logger.info("Stored chunks in Qdrant")


if __name__ == "__main__":
    main()