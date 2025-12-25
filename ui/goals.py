"""Goals management widget."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QComboBox, QCheckBox,
    QTextEdit, QGroupBox, QListWidget, QListWidgetItem
)
from PySide6.QtCore import Qt
from typing import Optional

from utils.logger import get_logger
from config.goals import get_goals, update_goals

logger = get_logger(__name__)


class GoalsWidget(QWidget):
    """Widget for managing goals."""
    
    def __init__(self, entity=None):
        super().__init__()
        self.entity = entity
        self.logger = logger
        
        self._init_ui()
        self.load_goals()
    
    def _init_ui(self):
        """Initialize UI."""
        layout = QVBoxLayout(self)
        
        # Quality settings
        quality_group = QGroupBox("Настройки качества")
        quality_layout = QVBoxLayout()
        
        quality_layout.addWidget(QLabel("Глобальное качество:"))
        self.quality_combo = QComboBox()
        self.quality_combo.addItems(["high", "medium", "low"])
        quality_layout.addWidget(self.quality_combo)
        
        quality_layout.addWidget(QLabel("Частота публикаций:"))
        self.frequency_combo = QComboBox()
        self.frequency_combo.addItems(["frequent", "moderate", "rare"])
        quality_layout.addWidget(self.frequency_combo)
        
        quality_layout.addWidget(QLabel("Стиль:"))
        self.style_edit = QLineEdit()
        quality_layout.addWidget(self.style_edit)
        
        quality_group.setLayout(quality_layout)
        layout.addWidget(quality_group)
        
        # Topics
        topics_group = QGroupBox("Темы")
        topics_layout = QVBoxLayout()
        
        topics_layout.addWidget(QLabel("Предпочитаемые темы (одна на строку):"))
        self.topics_edit = QTextEdit()
        self.topics_edit.setMaximumHeight(100)
        topics_layout.addWidget(self.topics_edit)
        
        topics_layout.addWidget(QLabel("Темы для избежания (одна на строку):"))
        self.avoid_topics_edit = QTextEdit()
        self.avoid_topics_edit.setMaximumHeight(100)
        topics_layout.addWidget(self.avoid_topics_edit)
        
        topics_group.setLayout(topics_layout)
        layout.addWidget(topics_group)
        
        # Options
        options_group = QGroupBox("Опции")
        options_layout = QVBoxLayout()
        
        self.avoid_repetition_check = QCheckBox("Избегать повторений")
        options_layout.addWidget(self.avoid_repetition_check)
        
        self.platform_optimization_check = QCheckBox("Оптимизация под платформы")
        options_layout.addWidget(self.platform_optimization_check)
        
        options_group.setLayout(options_layout)
        layout.addWidget(options_group)
        
        # Save button
        save_button = QPushButton("Сохранить цели")
        save_button.clicked.connect(self.save_goals)
        layout.addWidget(save_button)
        
        layout.addStretch()
    
    def load_goals(self):
        """Load goals from entity or config."""
        try:
            goals = get_goals()
            
            # Set quality
            index = self.quality_combo.findText(goals.global_quality)
            if index >= 0:
                self.quality_combo.setCurrentIndex(index)
            
            # Set frequency
            index = self.frequency_combo.findText(goals.posting_frequency)
            if index >= 0:
                self.frequency_combo.setCurrentIndex(index)
            
            # Set style
            self.style_edit.setText(goals.style_preference)
            
            # Set topics
            self.topics_edit.setPlainText("\n".join(goals.preferred_topics))
            self.avoid_topics_edit.setPlainText("\n".join(goals.avoid_topics))
            
            # Set options
            self.avoid_repetition_check.setChecked(goals.avoid_repetition)
            self.platform_optimization_check.setChecked(goals.platform_optimization)
            
        except Exception as e:
            self.logger.error(f"Error loading goals: {e}")
    
    def save_goals(self):
        """Save goals."""
        try:
            # Get topics (split by newline, filter empty)
            preferred_topics = [
                topic.strip()
                for topic in self.topics_edit.toPlainText().split("\n")
                if topic.strip()
            ]
            avoid_topics = [
                topic.strip()
                for topic in self.avoid_topics_edit.toPlainText().split("\n")
                if topic.strip()
            ]
            
            # Update goals
            update_goals(
                global_quality=self.quality_combo.currentText(),
                posting_frequency=self.frequency_combo.currentText(),
                style_preference=self.style_edit.text(),
                preferred_topics=preferred_topics,
                avoid_topics=avoid_topics,
                avoid_repetition=self.avoid_repetition_check.isChecked(),
                platform_optimization=self.platform_optimization_check.isChecked()
            )
            
            # Update entity if available
            if self.entity:
                self.entity.update_goals(
                    global_quality=self.quality_combo.currentText(),
                    posting_frequency=self.frequency_combo.currentText(),
                    style_preference=self.style_edit.text(),
                    preferred_topics=preferred_topics,
                    avoid_topics=avoid_topics,
                    avoid_repetition=self.avoid_repetition_check.isChecked(),
                    platform_optimization=self.platform_optimization_check.isChecked()
                )
            
            self.logger.info("Goals saved")
            
        except Exception as e:
            self.logger.error(f"Error saving goals: {e}")

