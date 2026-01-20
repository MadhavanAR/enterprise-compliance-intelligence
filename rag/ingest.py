from pathlib import Path
from langchain_text_splitters import RecursiveCharacterTextSplitter
from rag.store import store_chunks
from rag.logger import logger
from rag.metadata import normalize_text, create_metadata


def load_and_chunk(
    file_path: str = "data/aws_compliance.txt",
    author: str = None,
    source: str = None,
    document_id: str = None,
    version: str = "2025-01"
) -> list[tuple[str, dict]]:
    """
    Load and chunk document with metadata normalization.

    Returns:
        List of (chunk_text, metadata) tuples
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"Data file not found: {file_path}")

    text = path.read_text(encoding="utf-8")

    # Normalize text (remove citation artifacts, normalize whitespace)
    normalized_text = normalize_text(text)

    logger.info(f"Text normalized: {len(text)} -> {len(normalized_text)} chars")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=600,
        chunk_overlap=100
    )

    chunks = splitter.split_text(normalized_text)

    # ---- ENTERPRISE METADATA (DOCUMENT-LEVEL) ----
    metadata = create_metadata(
        author=author or "Amazon Web Services",
        source=source or "aws_compliance_programs",
        document_id=document_id or path.stem
    )

    # Extend with compliance-specific fields
    metadata.update({
        "vendor": "AWS",
        "document_type": "compliance",
        "url": "https://aws.amazon.com/compliance/programs/",
        "jurisdiction": "global",
        "version": version
    })

    logger.info(f"Total chunks created: {len(chunks)}")
    logger.debug(f"Metadata attached: {metadata}")

    chunks_with_metadata = [(chunk, metadata) for chunk in chunks]

    for i, (chunk, _) in enumerate(chunks_with_metadata):
        logger.debug(f"Chunk {i}: {chunk[:200]}")

    return chunks_with_metadata


def main():
    # READ_ONLY_MODE: Block ingestion in production
    from rag.config import READ_ONLY_MODE
    from rag.logger import logger as root_logger

    if READ_ONLY_MODE:
        root_logger.error("SECURITY: Ingestion blocked - READ_ONLY_MODE enabled")
        raise RuntimeError(
            "Ingestion is disabled in READ_ONLY_MODE. This is a security feature."
        )

    chunks_with_metadata = load_and_chunk()
    store_chunks(chunks_with_metadata)

    logger.info("Stored AWS compliance chunks in Qdrant with metadata")


if __name__ == "__main__":
    main()