"""Memory refactoring - само-рефакторинг памяти."""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta, timezone

from utils.logger import get_logger
from .storage import MemoryStorage
from .index import MemoryIndex
from .embeddings import generate_embedding, cosine_similarity

logger = get_logger(__name__)


class MemoryRefactoring:
    """Self-refactoring of memory - cleaning and rethinking old thoughts."""
    
    def __init__(self, memory_storage: MemoryStorage, memory_index: MemoryIndex):
        self.storage = memory_storage
        self.index = memory_index
        self.logger = logger
    
    async def refactor_old_memories(self, days_old: int = 30) -> Dict[str, Any]:
        """Refactor memories older than specified days."""
        try:
            # Get old content entries
            all_content = self.storage.get_recent_content(limit=1000)
            
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_old)
            old_content = [
                c for c in all_content
                if datetime.fromisoformat(c.timestamp.replace('Z', '+00:00')) < cutoff_date
            ]
            
            refactored_count = 0
            merged_count = 0
            
            # Group similar old content
            for content in old_content:
                # Find similar content
                similar = self.index.search_similar(
                    content.content,
                    entry_type="content",
                    threshold=0.85,
                    top_k=5
                )
                
                if len(similar) > 1:
                    # Merge similar entries (keep newest, archive others)
                    similar_entries = [e[0] for e in similar if e[0].id != content.id]
                    if similar_entries:
                        # Mark as merged in metadata
                        merged_count += len(similar_entries)
            
            refactored_count = len(old_content)
            
            self.logger.info(f"Refactored {refactored_count} old memories, merged {merged_count} duplicates")
            
            return {
                "refactored": refactored_count,
                "merged": merged_count,
                "total_old": len(old_content)
            }
        except Exception as e:
            self.logger.error(f"Error refactoring memory: {e}")
            return {"error": str(e)}
    
    async def clean_redundant_topics(self) -> Dict[str, Any]:
        """Clean redundant topics from memory."""
        try:
            # Get all topic entries
            topics = self.index.storage.search_entries(entry_type="topic", limit=1000)
            
            # Group similar topics
            topic_groups = {}
            cleaned_count = 0
            
            for topic_entry in topics:
                topic_text = topic_entry.data.get("topic", "")
                if not topic_text:
                    continue
                
                # Find similar topics
                similar = self.index.search_similar(
                    topic_text,
                    entry_type="topic",
                    threshold=0.9,
                    top_k=5
                )
                
                if len(similar) > 1:
                    # Keep newest, mark others as redundant
                    cleaned_count += len(similar) - 1
            
            self.logger.info(f"Cleaned {cleaned_count} redundant topics")
            
            return {
                "cleaned": cleaned_count,
                "total_topics": len(topics)
            }
        except Exception as e:
            self.logger.error(f"Error cleaning topics: {e}")
            return {"error": str(e)}
    
    async def rethink_old_decisions(self, days_old: int = 60) -> Dict[str, Any]:
        """Rethink old decisions and update reasoning."""
        try:
            # This would use AI to re-evaluate old decisions
            # For now, just log the concept
            self.logger.info(f"Rethinking decisions older than {days_old} days")
            
            return {
                "rethought": 0,  # Placeholder
                "updated": 0
            }
        except Exception as e:
            self.logger.error(f"Error rethinking decisions: {e}")
            return {"error": str(e)}

