"""Embeddings generation and similarity search."""

from typing import List, Optional
import numpy as np

from utils.logger import get_logger
from config.defaults import EMBEDDINGS_MODEL

logger = get_logger(__name__)

# Lazy loading of sentence transformer
_embedder = None


def get_embedder():
    """Get or create the embedder (lazy loading)."""
    global _embedder
    if _embedder is None:
        try:
            from sentence_transformers import SentenceTransformer
            _embedder = SentenceTransformer(EMBEDDINGS_MODEL)
            logger.info(f"Loaded embedding model: {EMBEDDINGS_MODEL}")
        except ImportError:
            logger.warning("sentence-transformers not available, embeddings disabled")
            return None
    return _embedder


def generate_embedding(text: str) -> Optional[List[float]]:
    """Generate embedding for text."""
    embedder = get_embedder()
    if embedder is None:
        return None
    
    try:
        embedding = embedder.encode(text, convert_to_numpy=True)
        return embedding.tolist()
    except Exception as e:
        logger.error(f"Error generating embedding: {e}")
        return None


def cosine_similarity(embedding1: List[float], embedding2: List[float]) -> float:
    """Calculate cosine similarity between two embeddings."""
    try:
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)
        
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return float(dot_product / (norm1 * norm2))
    except Exception as e:
        logger.error(f"Error calculating similarity: {e}")
        return 0.0


def find_similar(
    target_embedding: List[float],
    candidate_embeddings: List[tuple[str, List[float]]],
    threshold: float = 0.7,
    top_k: int = 5
) -> List[tuple[str, float]]:
    """Find similar embeddings."""
    similarities = []
    
    for candidate_id, candidate_embedding in candidate_embeddings:
        similarity = cosine_similarity(target_embedding, candidate_embedding)
        if similarity >= threshold:
            similarities.append((candidate_id, similarity))
    
    # Sort by similarity (descending)
    similarities.sort(key=lambda x: x[1], reverse=True)
    
    return similarities[:top_k]

