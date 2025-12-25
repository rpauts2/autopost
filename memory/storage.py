"""Memory storage with SQLite."""

import sqlite3
import json
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone

from utils.logger import get_logger
from .models import MemoryEntry, ContentMemory, DecisionMemory
from config.defaults import MEMORY_DB_PATH

logger = get_logger(__name__)


class MemoryStorage:
    """SQLite-based memory storage."""
    
    def __init__(self, db_path: Path = MEMORY_DB_PATH):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
    
    def _init_database(self):
        """Initialize database schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # General memory entries
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memory_entries (
                id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                entry_type TEXT NOT NULL,
                data TEXT NOT NULL,
                embedding TEXT,
                tags TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Content entries
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS content_entries (
                id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                topic TEXT NOT NULL,
                content TEXT NOT NULL,
                platform TEXT,
                style TEXT,
                quality_score REAL,
                published BOOLEAN DEFAULT 0,
                rejected BOOLEAN DEFAULT 0,
                rejection_reason TEXT,
                metrics TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Decision entries
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS decision_entries (
                id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                decision_type TEXT NOT NULL,
                context TEXT NOT NULL,
                decision TEXT NOT NULL,
                reasoning TEXT NOT NULL,
                outcome TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Indexes
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_entry_type 
            ON memory_entries(entry_type)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_timestamp 
            ON memory_entries(timestamp)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_content_published 
            ON content_entries(published)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_content_timestamp 
            ON content_entries(timestamp)
        """)
        
        conn.commit()
        conn.close()
        logger.info(f"Memory database initialized at {self.db_path}")
    
    def add_entry(self, entry: MemoryEntry) -> None:
        """Add a memory entry."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO memory_entries 
                (id, timestamp, entry_type, data, embedding, tags)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                entry.id,
                entry.timestamp,
                entry.entry_type,
                json.dumps(entry.data, ensure_ascii=False),
                json.dumps(entry.embedding) if entry.embedding else None,
                json.dumps(entry.tags, ensure_ascii=False) if entry.tags else None
            ))
            conn.commit()
            logger.debug(f"Added memory entry: {entry.id}")
        except Exception as e:
            logger.error(f"Error adding memory entry: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    def get_entry(self, entry_id: str) -> Optional[MemoryEntry]:
        """Get a memory entry by ID."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT * FROM memory_entries WHERE id = ?
            """, (entry_id,))
            row = cursor.fetchone()
            
            if row:
                return MemoryEntry(
                    id=row["id"],
                    timestamp=row["timestamp"],
                    entry_type=row["entry_type"],
                    data=json.loads(row["data"]),
                    embedding=json.loads(row["embedding"]) if row["embedding"] else None,
                    tags=json.loads(row["tags"]) if row["tags"] else []
                )
            return None
        except Exception as e:
            logger.error(f"Error getting memory entry: {e}")
            return None
        finally:
            conn.close()
    
    def search_entries(
        self,
        entry_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[MemoryEntry]:
        """Search memory entries."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            if entry_type:
                cursor.execute("""
                    SELECT * FROM memory_entries 
                    WHERE entry_type = ?
                    ORDER BY timestamp DESC
                    LIMIT ? OFFSET ?
                """, (entry_type, limit, offset))
            else:
                cursor.execute("""
                    SELECT * FROM memory_entries 
                    ORDER BY timestamp DESC
                    LIMIT ? OFFSET ?
                """, (limit, offset))
            
            entries = []
            for row in cursor.fetchall():
                entries.append(MemoryEntry(
                    id=row["id"],
                    timestamp=row["timestamp"],
                    entry_type=row["entry_type"],
                    data=json.loads(row["data"]),
                    embedding=json.loads(row["embedding"]) if row["embedding"] else None,
                    tags=json.loads(row["tags"]) if row["tags"] else []
                ))
            return entries
        except Exception as e:
            logger.error(f"Error searching memory entries: {e}")
            return []
        finally:
            conn.close()
    
    def add_content(self, content: ContentMemory) -> None:
        """Add content entry."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO content_entries
                (id, timestamp, topic, content, platform, style, quality_score,
                 published, rejected, rejection_reason, metrics)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                content.id,
                content.timestamp,
                content.topic,
                content.content,
                content.platform,
                content.style,
                content.quality_score,
                1 if content.published else 0,
                1 if content.rejected else 0,
                content.rejection_reason,
                json.dumps(content.metrics, ensure_ascii=False) if content.metrics else None
            ))
            conn.commit()
            logger.debug(f"Added content entry: {content.id}")
        except Exception as e:
            logger.error(f"Error adding content entry: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    def get_recent_content(self, limit: int = 50) -> List[ContentMemory]:
        """Get recent content entries."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT * FROM content_entries
                ORDER BY timestamp DESC
                LIMIT ?
            """, (limit,))
            
            contents = []
            for row in cursor.fetchall():
                contents.append(ContentMemory(
                    id=row["id"],
                    timestamp=row["timestamp"],
                    topic=row["topic"],
                    content=row["content"],
                    platform=row["platform"],
                    style=row["style"],
                    quality_score=row["quality_score"],
                    published=bool(row["published"]),
                    rejected=bool(row["rejected"]),
                    rejection_reason=row["rejection_reason"],
                    metrics=json.loads(row["metrics"]) if row["metrics"] else {}
                ))
            return contents
        except Exception as e:
            logger.error(f"Error getting recent content: {e}")
            return []
        finally:
            conn.close()
    
    def add_decision(self, decision: DecisionMemory) -> None:
        """Add decision entry."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO decision_entries
                (id, timestamp, decision_type, context, decision, reasoning, outcome)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                decision.id,
                decision.timestamp,
                decision.decision_type,
                json.dumps(decision.context, ensure_ascii=False),
                decision.decision,
                decision.reasoning,
                decision.outcome
            ))
            conn.commit()
            logger.debug(f"Added decision entry: {decision.id}")
        except Exception as e:
            logger.error(f"Error adding decision entry: {e}")
            conn.rollback()
        finally:
            conn.close()

