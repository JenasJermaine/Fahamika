"""
Fahamika Voice Pipeline — Pinecone Vector Search
Matches transcribed questions to the closest pre-approved civic content.
"""

import logging
from shared.config import config

logger = logging.getLogger(__name__)

# Lazy-loaded models and connections
_pinecone_index = None
_embedding_model_obj = None


def _get_pinecone_index():
    """Lazy-load the Pinecone index (imports pinecone only when first used)."""
    global _pinecone_index
    if _pinecone_index is not None:
        return _pinecone_index

    try:
        from pinecone import Pinecone
    except ImportError:
        raise ImportError(
            "Pinecone client not installed. Run: pip install pinecone"
        )

    pc = Pinecone(api_key=config.PINECONE_API_KEY)
    _pinecone_index = pc.Index(config.PINECONE_INDEX_NAME)
    logger.info(f"Connected to Pinecone index: {config.PINECONE_INDEX_NAME}")
    return _pinecone_index


def _get_embedding_model():
    """Lazy-load the HuggingFace embedding model (cached after first call)."""
    global _embedding_model_obj
    if _embedding_model_obj is not None:
        return _embedding_model_obj

    from sentence_transformers import SentenceTransformer

    model_name = config.EMBEDDING_MODEL
    logger.info(f"Loading embedding model: {model_name} ...")
    _embedding_model_obj = SentenceTransformer(model_name)
    logger.info(f"Embedding model '{model_name}' loaded.")
    return _embedding_model_obj


def _get_embedding(text: str) -> list[float]:
    """Generate an embedding vector for the given text using a local model."""
    model = _get_embedding_model()
    # E5 models expect "query: " prefix for search queries
    if "e5" in config.EMBEDDING_MODEL.lower():
        text = f"query: {text}"
    embedding = model.encode(text)
    return embedding.tolist()


def search(question: str, top_k: int = 3) -> list[dict]:
    """
    Search Pinecone for the closest civic content topics to the question.

    Args:
        question: The caller's transcribed question.
        top_k: Number of results to return.

    Returns:
        List of matched records, each with {id, topic, content, score}.
    """
    index = _get_pinecone_index()

    logger.info(f"Embedding question: {question[:80]}...")
    vector = _get_embedding(question)

    logger.info(f"Querying Pinecone (top_k={top_k}) ...")
    results = index.query(
        vector=vector,
        top_k=top_k,
        include_metadata=True,
        namespace="civic-content",
    )

    matches = []
    for match in results.matches:
        matches.append({
            "id": match.id,
            "topic": match.metadata.get("topic", ""),
            "content": match.metadata.get("content", ""),
            "language": match.metadata.get("language", "en"),
            "score": match.score,
        })

    logger.info(f"Pinecone returned {len(matches)} matches.")
    if matches:
        logger.info(f"Top match: {matches[0]['topic']} (score={matches[0]['score']:.3f})")

    return matches


def build_retrieval_context(matches: list[dict], min_score: float = 0.5) -> str | None:
    """
    Build a combined context string from matched content for the LLM.
    Returns None if no match meets the minimum score threshold.
    """
    relevant = [m for m in matches if m["score"] >= min_score]

    if not relevant:
        return None

    # Take the top match's content
    best = relevant[0]
    return f"TOPIC: {best['topic']}\n\nCONTENT: {best['content']}"
