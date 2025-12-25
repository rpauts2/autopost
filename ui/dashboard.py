"""Dashboard widget."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTextEdit, QGroupBox, QGridLayout
)
from PySide6.QtCore import Qt, Signal, QObject
from typing import Optional, Dict, Any

from utils.logger import get_logger

logger = get_logger(__name__)


class DashboardWidget(QWidget):
    """Dashboard showing entity status."""
    
    def __init__(self, entity=None, signals=None):
        super().__init__()
        self.entity = entity
        self.signals = signals
        self.logger = logger
        
        self._init_ui()
        
        # Connect signals
        if signals:
            signals.status_updated.connect(self.on_status_updated)
            signals.metrics_updated.connect(self.on_metrics_updated)
    
    def _init_ui(self):
        """Initialize UI."""
        layout = QVBoxLayout(self)
        
        # Status section
        status_group = QGroupBox("Статус сущности")
        status_layout = QGridLayout()
        
        self.status_label = QLabel("Не инициализировано")
        self.status_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        status_layout.addWidget(QLabel("Статус:"), 0, 0)
        status_layout.addWidget(self.status_label, 0, 1)
        
        self.intent_label = QLabel("-")
        status_layout.addWidget(QLabel("Текущее намерение:"), 1, 0)
        status_layout.addWidget(self.intent_label, 1, 1)
        
        self.running_label = QLabel("Нет")
        status_layout.addWidget(QLabel("Работает:"), 2, 0)
        status_layout.addWidget(self.running_label, 2, 1)
        
        status_group.setLayout(status_layout)
        layout.addWidget(status_group)
        
        # Metrics section
        metrics_group = QGroupBox("Метрики")
        metrics_layout = QGridLayout()
        
        self.cycles_label = QLabel("0")
        metrics_layout.addWidget(QLabel("Циклов завершено:"), 0, 0)
        metrics_layout.addWidget(self.cycles_label, 0, 1)
        
        self.content_created_label = QLabel("0")
        metrics_layout.addWidget(QLabel("Контента создано:"), 1, 0)
        metrics_layout.addWidget(self.content_created_label, 1, 1)
        
        self.content_published_label = QLabel("0")
        metrics_layout.addWidget(QLabel("Опубликовано:"), 2, 0)
        metrics_layout.addWidget(self.content_published_label, 2, 1)
        
        self.content_rejected_label = QLabel("0")
        metrics_layout.addWidget(QLabel("Отклонено:"), 3, 0)
        metrics_layout.addWidget(self.content_rejected_label, 3, 1)
        
        metrics_group.setLayout(metrics_layout)
        layout.addWidget(metrics_group)
        
        # Control buttons
        button_layout = QHBoxLayout()
        
        self.start_button = QPushButton("Запустить")
        self.start_button.clicked.connect(self.on_start_clicked)
        button_layout.addWidget(self.start_button)
        
        self.stop_button = QPushButton("Остановить")
        self.stop_button.clicked.connect(self.on_stop_clicked)
        self.stop_button.setEnabled(False)
        button_layout.addWidget(self.stop_button)
        
        layout.addLayout(button_layout)
        
        # Activity log
        log_group = QGroupBox("Журнал активности")
        log_layout = QVBoxLayout()
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(200)
        log_layout.addWidget(self.log_text)
        
        log_group.setLayout(log_layout)
        layout.addWidget(log_group)
        
        layout.addStretch()
        
        # Initial update
        self.update_display()
    
    def on_status_updated(self, status: Dict[str, Any]):
        """Handle status update."""
        self.status_label.setText(status.get("status", "unknown"))
        self.intent_label.setText(status.get("current_intent", "-") or "-")
        self.running_label.setText("Да" if status.get("running") else "Нет")
        
        # Update buttons
        running = status.get("running", False)
        self.start_button.setEnabled(not running)
        self.stop_button.setEnabled(running)
    
    def on_metrics_updated(self, metrics: Dict[str, Any]):
        """Handle metrics update."""
        self.cycles_label.setText(str(metrics.get("cycles_completed", 0)))
        self.content_created_label.setText(str(metrics.get("content_created", 0)))
        self.content_published_label.setText(str(metrics.get("content_published", 0)))
        self.content_rejected_label.setText(str(metrics.get("content_rejected", 0)))
    
    def update_display(self):
        """Update display with current entity status."""
        if self.entity:
            try:
                status = self.entity.get_status()
                self.on_status_updated(status)
                if 'metrics' in status:
                    self.on_metrics_updated(status['metrics'])
            except Exception as e:
                self.logger.error(f"Error updating display: {e}")
    
    def on_start_clicked(self):
        """Handle start button click."""
        if self.entity:
            try:
                import asyncio
                import threading
                
                def start_entity():
                    try:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        
                        # Initialize if needed
                        if not hasattr(self.entity, 'initialized') or not self.entity.initialized:
                            loop.run_until_complete(self.entity.initialize())
                        
                        # Start entity (this will start scheduler and trigger first cycle)
                        loop.run_until_complete(self.entity.start())
                        
                        # Keep loop running to allow async tasks
                        try:
                            # Run for a while to allow tasks to complete
                            loop.run_until_complete(asyncio.sleep(1))  # Give it a moment
                            # Don't run forever - let tasks complete naturally
                        except KeyboardInterrupt:
                            pass
                        except Exception as e:
                            self.logger.error(f"Loop error: {e}")
                        finally:
                            # Don't close immediately - let tasks finish
                            pass
                    except Exception as e:
                        self.logger.error(f"Error starting entity: {e}", exc_info=True)
                        import traceback
                        traceback.print_exc()
                
                thread = threading.Thread(target=start_entity, daemon=True)
                thread.start()
                self.log_text.append("✅ Сущность запущена. Генерация контента начата...")
            except Exception as e:
                self.logger.error(f"Error starting entity: {e}")
                self.log_text.append(f"❌ Ошибка запуска: {e}")
    
    def on_stop_clicked(self):
        """Handle stop button click."""
        if self.entity:
            try:
                import asyncio
                import threading
                
                def stop_entity():
                    try:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        loop.run_until_complete(self.entity.stop())
                        loop.close()
                    except Exception as e:
                        self.logger.error(f"Error stopping entity: {e}")
                
                thread = threading.Thread(target=stop_entity, daemon=True)
                thread.start()
                self.log_text.append("Сущность остановлена")
            except Exception as e:
                self.logger.error(f"Error stopping entity: {e}")
                self.log_text.append(f"Ошибка остановки: {e}")

