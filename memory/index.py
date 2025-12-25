"""Memory indexing and search."""

from typing import List, Optional, Dict, Any
from .storage import MemoryStorage
from .embeddings import generate_embedding, find_similar
from .models import MemoryEntry
from utils.logger import get_logger

logger = get_logger(__name__)


class MemoryIndex:
    """Memory index for semantic search."""
    
    def __init__(self, storage: MemoryStorage):
        self.storage = storage
        self.logger = logger
    
    def add_with_embedding(self, entry: MemoryEntry, generate: bool = True) -> None:
        """Add entry with embedding generation."""
        if generate and entry.embedding is None:
            # Generate embedding from data if possible
            text_to_embed = self._extract_text_for_embedding(entry)
            if text_to_embed:
                entry.embedding = generate_embedding(text_to_embed)
        
        self.storage.add_entry(entry)
    
    def _extract_text_for_embedding(self, entry: MemoryEntry) -> Optional[str]:
        """Extract text from entry data for embedding."""
        if entry.entry_type == "topic":
            return entry.data.get("topic", "")
        elif entry.entry_type == "content":
            return entry.data.get("content", "") or entry.data.get("text", "")
        elif entry.entry_type == "rejection":
            return entry.data.get("reason", "") or entry.data.get("topic", "")
        else:
            # Try to find any text field
            for key in ["text", "content", "topic", "title", "description"]:
                if key in entry.data and isinstance(entry.data[key], str):
                    return entry.data[key]
        return None
    
    def search_similar(
        self,
        query: str,
        entry_type: Optional[str] = None,
        threshold: float = 0.7,
        top_k: int = 5
    ) -> List[tuple[MemoryEntry, float]]:
        """Search for similar entries by semantic similarity."""
        # Generate query embedding
        query_embedding = generate_embedding(query)
        if query_embedding is None:
            self.logger.warning("Could not generate query embedding")
            return []
        
        # Get candidates
        candidates = self.storage.search_entries(entry_type=entry_type, limit=1000)
        
        # Filter entries with embeddings
        candidates_with_embeddings = [
            (entry.id, entry.embedding)
            for entry in candidates
            if entry.embedding is not None
        ]
        
        if not candidates_with_embeddings:
            return []
        
        # Find similar
        similar_ids = find_similar(
            query_embedding,
            candidates_with_embeddings,
            threshold=threshold,
            top_k=top_k
        )
        
        # Map back to entries
        entry_map = {entry.id: entry for entry in candidates}
        results = [
            (entry_map[entry_id], similarity)
            for entry_id, similarity in similar_ids
            if entry_id in entry_map
        ]
        
        return results
    
    def check_repetition(
        self,
        text: str,
        threshold: float = 0.85
    ) -> tuple[bool, Optional[MemoryEntry]]:
        """Check if text is too similar to existing content."""
        similar = self.search_similar(text, threshold=threshold, top_k=1)
        
        if similar and similar[0][1] >= threshold:
            return True, similar[0][0]
        return False, None

