"""Thematic cluster management - мыслительные ветки."""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
from pathlib import Path

from utils.logger import get_logger
from utils.helpers import get_timestamp
from memory.embeddings import generate_embedding, cosine_similarity
from config.defaults import DATA_DIR

logger = get_logger(__name__)

CLUSTERS_FILE = DATA_DIR / "clusters.json"


@dataclass
class TopicCluster:
    """Thematic cluster (мыслительная ветка)."""
    id: str
    name: str
    description: str
    topics: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=get_timestamp)
    last_used: str = field(default_factory=get_timestamp)
    depth: int = 0  # How deep we've gone into this cluster
    active: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


class ClusterManager:
    """Manages thematic clusters."""
    
    def __init__(self, memory_index=None):
        self.memory_index = memory_index
        self.clusters: Dict[str, TopicCluster] = {}
        self.logger = logger
        self._load_clusters()
    
    def _load_clusters(self):
        """Load clusters from file."""
        if CLUSTERS_FILE.exists():
            try:
                with open(CLUSTERS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for cluster_id, cluster_data in data.items():
                        self.clusters[cluster_id] = TopicCluster(**cluster_data)
                self.logger.info(f"Loaded {len(self.clusters)} clusters")
            except Exception as e:
                self.logger.error(f"Error loading clusters: {e}")
    
    def _save_clusters(self):
        """Save clusters to file."""
        try:
            CLUSTERS_FILE.parent.mkdir(parents=True, exist_ok=True)
            data = {
                cluster_id: {
                    "id": cluster.id,
                    "name": cluster.name,
                    "description": cluster.description,
                    "topics": cluster.topics,
                    "created_at": cluster.created_at,
                    "last_used": cluster.last_used,
                    "depth": cluster.depth,
                    "active": cluster.active,
                    "metadata": cluster.metadata
                }
                for cluster_id, cluster in self.clusters.items()
            }
            with open(CLUSTERS_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"Error saving clusters: {e}")
    
    def find_cluster_for_topic(self, topic: str, threshold: float = 0.7) -> Optional[TopicCluster]:
        """Find existing cluster for a topic."""
        if not topic or not self.clusters:
            return None
        
        topic_embedding = generate_embedding(topic)
        if not topic_embedding:
            return None
        
        best_cluster = None
        best_similarity = 0.0
        
        for cluster in self.clusters.values():
            if not cluster.active:
                continue
            
            # Check similarity with cluster topics
            for cluster_topic in cluster.topics[-5:]:  # Check last 5 topics
                cluster_embedding = generate_embedding(cluster_topic)
                if cluster_embedding:
                    similarity = cosine_similarity(topic_embedding, cluster_embedding)
                    if similarity > best_similarity:
                        best_similarity = similarity
                        best_cluster = cluster
        
        if best_similarity >= threshold:
            return best_cluster
        
        return None
    
    def create_cluster(self, topic: str, description: str = "") -> TopicCluster:
        """Create a new cluster."""
        from utils.helpers import generate_id
        
        cluster = TopicCluster(
            id=generate_id("cluster_"),
            name=topic[:50],
            description=description or f"Кластер для темы: {topic}",
            topics=[topic],
            depth=0
        )
        
        self.clusters[cluster.id] = cluster
        self._save_clusters()
        self.logger.info(f"Created new cluster: {cluster.name}")
        
        return cluster
    
    def add_topic_to_cluster(self, cluster_id: str, topic: str):
        """Add topic to cluster and increase depth."""
        if cluster_id in self.clusters:
            cluster = self.clusters[cluster_id]
            cluster.topics.append(topic)
            cluster.depth += 1
            cluster.last_used = get_timestamp()
            self._save_clusters()
            self.logger.debug(f"Added topic to cluster {cluster.name}, depth: {cluster.depth}")
    
    def get_active_clusters(self) -> List[TopicCluster]:
        """Get active clusters."""
        return [c for c in self.clusters.values() if c.active]
    
    def get_cluster_for_development(self) -> Optional[TopicCluster]:
        """Get cluster that should be developed further."""
        active = self.get_active_clusters()
        if not active:
            return None
        
        # Prefer clusters that:
        # 1. Haven't been used recently
        # 2. Have moderate depth (not too shallow, not too deep)
        # 3. Are active
        
        best_cluster = None
        best_score = -1
        
        for cluster in active:
            # Calculate score (lower is better for selection)
            # Want clusters with depth 2-5, recently used but not too recently
            depth_score = abs(cluster.depth - 3)  # Prefer depth ~3
            recency_score = 0  # Would calculate from last_used timestamp
            
            score = depth_score  # Simplified for now
            if score < best_score or best_score == -1:
                best_score = score
                best_cluster = cluster
        
        return best_cluster
    
    def evolve_cluster(self, cluster_id: str, new_topic: str):
        """Evolve cluster with new related topic."""
        if cluster_id in self.clusters:
            cluster = self.clusters[cluster_id]
            
            # Add topic
            self.add_topic_to_cluster(cluster_id, new_topic)
            
            # Update metadata
            cluster.metadata["evolution_count"] = cluster.metadata.get("evolution_count", 0) + 1
            
            self._save_clusters()

