from pathlib import Path
from langchain_text_splitters import RecursiveCharacterTextSplitter
from rag.store import store_chunks
from rag.logger import logger
from rag.metadata import normalize_text, create_metadata


def load_and_chunk(
    file_path: str = "data/sample_doc.txt",
    author: str = None,
    source: str = None,
    document_id: str = None
) -> list[tuple[str, dict]]:
    """
    Load and chunk document with metadata normalization.
    
    Returns:
        List of (chunk_text, metadata) tuples
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"Data file not found: {file_path}")

    text = path.read_text()
    
    # Normalize text (remove citation artifacts, normalize whitespace)
    normalized_text = normalize_text(text)
    
    logger.info(f"Text normalized: {len(text)} -> {len(normalized_text)} chars")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=600,
        chunk_overlap=100
    )

    chunks = splitter.split_text(normalized_text)

    # Create metadata for document
    source_value = source or str(file_path)
    document_id_value = document_id or str(path.stem)
    
    metadata = create_metadata(
        author=author,
        source=source_value,
        document_id=document_id_value
    )

    logger.info(f"Total chunks created: {len(chunks)}")
    logger.debug(f"Metadata: {metadata}")

    # Return chunks with metadata
    chunks_with_metadata = [(chunk, metadata) for chunk in chunks]
    
    for i, (chunk, _) in enumerate(chunks_with_metadata):
        logger.debug(f"Chunk {i}: {chunk[:200]}")

    return chunks_with_metadata


def main():
    chunks_with_metadata = load_and_chunk()
    # Extract just chunks for backward compatibility with store_chunks
    chunks = [chunk for chunk, _ in chunks_with_metadata]
    store_chunks(chunks_with_metadata)
    logger.info("Stored chunks in Qdrant with metadata")


if __name__ == "__main__":
    main()