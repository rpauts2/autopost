"""Semantic Map visualization widget."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QGroupBox, QTextEdit, QPushButton
)
from PySide6.QtCore import Qt
from typing import Optional, List, Dict, Any

from utils.logger import get_logger

logger = get_logger(__name__)


class SemanticMapWidget(QWidget):
    """Widget for semantic map visualization."""
    
    def __init__(self, entity=None):
        super().__init__()
        self.entity = entity
        self.logger = logger
        self._init_ui()
    
    def _init_ui(self):
        """Initialize UI."""
        layout = QVBoxLayout(self)
        
        # Info
        info_group = QGroupBox("Карта смыслов")
        info_layout = QVBoxLayout()
        
        info_layout.addWidget(QLabel(
            "Карта смыслов визуализирует раскрытые идеи и их связи.\n"
            "Помогает понять развитие системы и избежать повторений."
        ))
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        # Map display (simplified - would use matplotlib or graphviz in production)
        map_group = QGroupBox("Визуализация")
        map_layout = QVBoxLayout()
        
        self.map_display = QTextEdit()
        self.map_display.setReadOnly(True)
        self.map_display.setMinimumHeight(400)
        map_layout.addWidget(self.map_display)
        
        refresh_button = QPushButton("Обновить карту")
        refresh_button.clicked.connect(self.update_map)
        map_layout.addWidget(refresh_button)
        
        map_group.setLayout(map_layout)
        layout.addWidget(map_group)
        
        # Statistics
        stats_group = QGroupBox("Статистика")
        stats_layout = QVBoxLayout()
        
        self.stats_text = QTextEdit()
        self.stats_text.setReadOnly(True)
        self.stats_text.setMaximumHeight(150)
        stats_layout.addWidget(self.stats_text)
        
        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)
        
        # Initial update
        self.update_map()
    
    def update_map(self):
        """Update semantic map."""
        if not self.entity or not hasattr(self.entity, 'cluster_manager'):
            self.map_display.setText("Entity не доступен")
            return
        
        try:
            clusters = self.entity.cluster_manager.get_active_clusters()
            
            # Generate simple text representation
            map_text = "=== КАРТА СМЫСЛОВ ===\n\n"
            
            if clusters:
                map_text += f"Активных кластеров: {len(clusters)}\n\n"
                
                for cluster in clusters:
                    map_text += f"📁 {cluster.name}\n"
                    map_text += f"   Описание: {cluster.description}\n"
                    map_text += f"   Глубина: {cluster.depth}\n"
                    map_text += f"   Тем: {len(cluster.topics)}\n"
                    if cluster.topics:
                        map_text += f"   Последние темы:\n"
                        for topic in cluster.topics[-3:]:
                            map_text += f"     - {topic[:50]}\n"
                    map_text += "\n"
            else:
                map_text += "Кластеры еще не созданы.\n"
            
            # Add statistics
            stats_text = f"""СТАТИСТИКА:
Активных кластеров: {len(clusters)}
Всего тем раскрыто: {sum(len(c.topics) for c in clusters)}
Средняя глубина кластера: {sum(c.depth for c in clusters) / len(clusters) if clusters else 0:.1f}
"""
            self.stats_text.setText(stats_text)
            
            self.map_display.setText(map_text)
        except Exception as e:
            self.logger.error(f"Error updating semantic map: {e}")
            self.map_display.setText(f"Ошибка: {e}")

