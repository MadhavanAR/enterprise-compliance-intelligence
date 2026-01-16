"""
Metadata handling: normalization, validation, and filtering
"""
import re
from typing import Dict, Any, Optional, List
from rag.logger import get_logger

logger = get_logger()

def normalize_text(text: str) -> str:
    """
    Normalize text during ingestion.
    
    - Normalize whitespace
    - Remove duplicate newlines
    - Strip citation artifacts (e.g., [1], (2), etc.)
    """
    # Normalize whitespace (multiple spaces -> single space)
    text = re.sub(r' +', ' ', text)
    
    # Remove duplicate newlines (3+ -> 2, 2 -> 1)
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'\n{2}', '\n', text)
    
    # Strip citation artifacts (e.g., [1], (2), [3], etc.)
    text = re.sub(r'\[(\d+)\]', '', text)  # [1], [2], etc.
    text = re.sub(r'\((\d+)\)', '', text)  # (1), (2), etc.
    
    # Trim
    text = text.strip()
    
    return text

def validate_metadata(metadata: Dict[str, Any]) -> bool:
    """
    Validate metadata to prevent empty or malformed values.
    
    Returns:
        True if valid, False otherwise
    """
    if not isinstance(metadata, dict):
        return False
    
    # Check for required fields (if present, must be non-empty)
    required_fields = ["author", "source", "document_id"]
    for field in required_fields:
        if field in metadata:
            value = metadata.get(field)
            if not value or (isinstance(value, str) and not value.strip()):
                logger.warning(f"Invalid metadata: {field} is empty", field=field)
                return False
    
    return True

def create_metadata(
    author: Optional[str] = None,
    source: Optional[str] = None,
    document_id: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Create metadata with validation.
    
    Args:
        author: Document author
        source: Document source (file path, URL, etc.)
        document_id: Unique document identifier
        **kwargs: Additional metadata fields
    
    Returns:
        Validated metadata dict
    """
    metadata = {
        "author": author or "unknown",
        "source": source or "unknown",
        "document_id": document_id or "unknown",
        **kwargs
    }
    
    if not validate_metadata(metadata):
        logger.warning("Metadata validation failed, using defaults")
        return {
            "author": "unknown",
            "source": "unknown",
            "document_id": "unknown"
        }
    
    return metadata

def format_metadata_filter(metadata_filters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format metadata filters for Qdrant query.
    
    Converts simple key-value pairs to Qdrant filter format.
    """
    if not metadata_filters:
        return {}
    
    # Qdrant filter format (must match payload structure)
    must_conditions = []
    
    for key, value in metadata_filters.items():
        must_conditions.append({
            "key": key,
            "match": {"value": value}
        })
    
    if not must_conditions:
        return {}
    
    return {
        "must": must_conditions
    }
