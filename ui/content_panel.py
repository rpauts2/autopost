"""Content generation and preview panel."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTextEdit, QGroupBox, QComboBox,
    QSpinBox, QCheckBox
)
from PySide6.QtCore import Qt, QTimer
from typing import Optional, Dict
import asyncio
import threading

from utils.logger import get_logger

logger = get_logger(__name__)


class ContentPanelWidget(QWidget):
    """Widget for content generation and preview."""
    
    def __init__(self, entity=None):
        super().__init__()
        self.entity = entity
        self.logger = logger
        self._init_ui()
    
    def _init_ui(self):
        """Initialize UI."""
        layout = QVBoxLayout(self)
        
        # Generation controls
        controls_group = QGroupBox("Генерация контента")
        controls_layout = QVBoxLayout()
        
        # Topic source
        controls_layout.addWidget(QLabel("Источник темы:"))
        self.topic_source_combo = QComboBox()
        self.topic_source_combo.addItems(["Автоматически", "По новостям", "Вручную"])
        controls_layout.addWidget(self.topic_source_combo)
        
        # Manual topic input
        controls_layout.addWidget(QLabel("Тема (если вручную):"))
        self.manual_topic_edit = QTextEdit()
        self.manual_topic_edit.setMaximumHeight(60)
        self.manual_topic_edit.setPlaceholderText("Введите тему для контента...")
        controls_layout.addWidget(self.manual_topic_edit)
        
        # Generate button
        generate_button = QPushButton("Сгенерировать контент")
        generate_button.clicked.connect(self.generate_content)
        controls_layout.addWidget(generate_button)
        
        controls_group.setLayout(controls_layout)
        layout.addWidget(controls_group)
        
        # Preview
        preview_group = QGroupBox("Предпросмотр")
        preview_layout = QVBoxLayout()
        
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setMinimumHeight(300)
        preview_layout.addWidget(self.preview_text)
        
        # Platform preview selector
        platform_layout = QHBoxLayout()
        platform_layout.addWidget(QLabel("Платформа:"))
        self.preview_platform_combo = QComboBox()
        self.preview_platform_combo.addItems(["Все", "VK", "Telegram", "Dzen"])
        self.preview_platform_combo.currentTextChanged.connect(self.update_preview)
        platform_layout.addWidget(self.preview_platform_combo)
        platform_layout.addStretch()
        preview_layout.addLayout(platform_layout)
        
        preview_group.setLayout(preview_layout)
        layout.addWidget(preview_group)
        
        # Actions
        actions_group = QGroupBox("Действия")
        actions_layout = QHBoxLayout()
        
        publish_button = QPushButton("Опубликовать")
        publish_button.clicked.connect(self.publish_content)
        actions_layout.addWidget(publish_button)
        
        save_button = QPushButton("Сохранить как черновик")
        save_button.clicked.connect(self.save_draft)
        actions_layout.addWidget(save_button)
        
        discard_button = QPushButton("Отменить")
        discard_button.clicked.connect(self.discard_content)
        actions_layout.addWidget(discard_button)
        
        actions_group.setLayout(actions_layout)
        layout.addWidget(actions_group)
        
        layout.addStretch()
    
    def generate_content(self):
        """Generate content."""
        if not self.entity:
            self.logger.warning("Entity not available")
            return
        
        topic_source = self.topic_source_combo.currentText()
        
        # Trigger content creation cycle
        def generate():
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                # Run content creation cycle
                context = {
                    "entity": self.entity,
                    "goals": self.entity.goals,
                    "settings": self.entity.settings,
                    "manual_topic": self.manual_topic_edit.toPlainText() if topic_source == "Вручную" else None
                }
                
                result = loop.run_until_complete(
                    self.entity.orchestrator.execute_content_creation_pipeline(context)
                )
                loop.close()
                
                # Update preview
                QTimer.singleShot(0, lambda: self.update_preview_from_result(result))
            except Exception as e:
                self.logger.error(f"Error generating content: {e}")
        
        thread = threading.Thread(target=generate, daemon=True)
        thread.start()
        self.preview_text.setText("Генерация контента...")
    
    def update_preview_from_result(self, result: Dict):
        """Update preview from generation result."""
        # Extract content from result
        # This is a simplified version
        content = "Контент сгенерирован"
        self.preview_text.setText(content)
    
    def update_preview(self):
        """Update preview for selected platform."""
        # Update preview based on platform selection
        pass
    
    def publish_content(self):
        """Publish current content."""
        self.logger.info("Publish content")
        # Implementation would trigger publisher agent
    
    def save_draft(self):
        """Save as draft."""
        self.logger.info("Save draft")
        # Implementation would save to drafts
    
    def discard_content(self):
        """Discard current content."""
        self.preview_text.clear()

