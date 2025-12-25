"""History panel - список постов и фильтрация."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTextEdit, QGroupBox, QComboBox,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QDateEdit, QLineEdit
)
from PySide6.QtCore import Qt, QDate
from typing import Optional, List, Dict, Any
from datetime import datetime

from utils.logger import get_logger

logger = get_logger(__name__)


class HistoryPanelWidget(QWidget):
    """Widget for viewing post history."""
    
    def __init__(self, entity=None):
        super().__init__()
        self.entity = entity
        self.logger = logger
        self._init_ui()
        self.load_history()
    
    def _init_ui(self):
        """Initialize UI."""
        layout = QVBoxLayout(self)
        
        # Filters
        filters_group = QGroupBox("Фильтры")
        filters_layout = QVBoxLayout()
        
        # Platform filter
        platform_layout = QHBoxLayout()
        platform_layout.addWidget(QLabel("Платформа:"))
        self.platform_filter = QComboBox()
        self.platform_filter.addItems(["Все", "VK", "Telegram", "Dzen"])
        self.platform_filter.currentTextChanged.connect(self.apply_filters)
        platform_layout.addWidget(self.platform_filter)
        platform_layout.addStretch()
        filters_layout.addLayout(platform_layout)
        
        # Status filter
        status_layout = QHBoxLayout()
        status_layout.addWidget(QLabel("Статус:"))
        self.status_filter = QComboBox()
        self.status_filter.addItems(["Все", "Опубликовано", "Отклонено", "Черновик"])
        self.status_filter.currentTextChanged.connect(self.apply_filters)
        status_layout.addWidget(self.status_filter)
        status_layout.addStretch()
        filters_layout.addLayout(status_layout)
        
        # Date range
        date_layout = QHBoxLayout()
        date_layout.addWidget(QLabel("От:"))
        self.date_from = QDateEdit()
        self.date_from.setDate(QDate.currentDate().addDays(-30))
        self.date_from.dateChanged.connect(self.apply_filters)
        date_layout.addWidget(self.date_from)
        
        date_layout.addWidget(QLabel("До:"))
        self.date_to = QDateEdit()
        self.date_to.setDate(QDate.currentDate())
        self.date_to.dateChanged.connect(self.apply_filters)
        date_layout.addWidget(self.date_to)
        
        date_layout.addStretch()
        filters_layout.addLayout(date_layout)
        
        # Search
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Поиск:"))
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Поиск по теме или содержанию...")
        self.search_edit.textChanged.connect(self.apply_filters)
        search_layout.addWidget(self.search_edit)
        filters_layout.addLayout(search_layout)
        
        filters_group.setLayout(filters_layout)
        layout.addWidget(filters_group)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Дата",
            "Тема",
            "Платформа",
            "Статус",
            "Качество",
            "Действия"
        ])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        layout.addWidget(self.table)
        
        # Details
        details_group = QGroupBox("Детали")
        details_layout = QVBoxLayout()
        
        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        self.details_text.setMaximumHeight(200)
        details_layout.addWidget(self.details_text)
        
        details_group.setLayout(details_layout)
        layout.addWidget(details_group)
    
    def load_history(self):
        """Load post history."""
        if not self.entity or not hasattr(self.entity, 'memory_storage'):
            return
        
        try:
            content_entries = self.entity.memory_storage.get_recent_content(limit=100)
            self.populate_table(content_entries)
        except Exception as e:
            self.logger.error(f"Error loading history: {e}")
    
    def populate_table(self, entries: List):
        """Populate table with entries."""
        self.table.setRowCount(len(entries))
        
        for row, entry in enumerate(entries):
            # Date
            try:
                date = datetime.fromisoformat(entry.timestamp.replace('Z', '+00:00'))
                date_item = QTableWidgetItem(date.strftime("%Y-%m-%d %H:%M"))
            except:
                date_item = QTableWidgetItem(entry.timestamp)
            self.table.setItem(row, 0, date_item)
            
            # Topic
            topic_item = QTableWidgetItem(entry.topic[:50] if entry.topic else "")
            self.table.setItem(row, 1, topic_item)
            
            # Platform
            platform_item = QTableWidgetItem(entry.platform or "")
            self.table.setItem(row, 2, platform_item)
            
            # Status
            if entry.published:
                status = "Опубликовано"
            elif entry.rejected:
                status = f"Отклонено: {entry.rejection_reason[:30] if entry.rejection_reason else ''}"
            else:
                status = "Черновик"
            status_item = QTableWidgetItem(status)
            self.table.setItem(row, 3, status_item)
            
            # Quality
            quality = entry.quality_score if entry.quality_score else 0.0
            quality_item = QTableWidgetItem(f"{quality:.2f}")
            self.table.setItem(row, 4, quality_item)
            
            # Actions
            view_button = QPushButton("Просмотр")
            view_button.clicked.connect(lambda checked, e=entry: self.view_details(e))
            self.table.setCellWidget(row, 5, view_button)
        
        # Resize columns
        self.table.resizeColumnsToContents()
    
    def apply_filters(self):
        """Apply filters to history."""
        # Filter logic would be implemented here
        self.load_history()
    
    def view_details(self, entry):
        """View entry details."""
        details = f"""Тема: {entry.topic}
Платформа: {entry.platform}
Дата: {entry.timestamp}
Статус: {'Опубликовано' if entry.published else 'Отклонено' if entry.rejected else 'Черновик'}
Качество: {entry.quality_score or 'N/A'}
Длина: {entry.metrics.get('content_length', 'N/A')}

Контент:
{entry.content[:500]}...

Причина отклонения: {entry.rejection_reason or 'N/A'}
"""
        self.details_text.setText(details)

