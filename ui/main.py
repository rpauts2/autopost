"""Main UI window."""

import sys
import asyncio
from typing import Optional
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QTabWidget, QStatusBar, QLabel
)
from PySide6.QtCore import Qt, QTimer, Signal, QObject
from PySide6.QtGui import QIcon

from utils.logger import get_logger
from ui.dashboard import DashboardWidget
from ui.goals import GoalsWidget
from ui.platforms_panel import PlatformsPanelWidget
from ui.content_panel import ContentPanelWidget
from ui.history_panel import HistoryPanelWidget
from ui.widgets.semantic_map import SemanticMapWidget
from ui.widgets.settings_panel import SettingsPanelWidget

logger = get_logger(__name__)


class EntitySignals(QObject):
    """Signals for entity updates."""
    status_updated = Signal(dict)
    metrics_updated = Signal(dict)


class MainWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self, entity=None):
        super().__init__()
        self.entity = entity
        self.signals = EntitySignals()
        self.logger = logger
        
        self.setWindowTitle("AutoPosst - Автономная AI Content Entity")
        self.setMinimumSize(1000, 700)
        
        # Create central widget with tabs
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        layout = QVBoxLayout(self.central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Tabs
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        # Dashboard tab
        self.dashboard = DashboardWidget(entity=entity, signals=self.signals)
        self.tabs.addTab(self.dashboard, "Dashboard")
        
        # Goals tab
        self.goals_widget = GoalsWidget(entity=entity)
        self.tabs.addTab(self.goals_widget, "Цели")
        
        # Platforms tab
        self.platforms_panel = PlatformsPanelWidget(entity=entity)
        self.tabs.addTab(self.platforms_panel, "Платформы")
        
        # Content tab
        self.content_panel = ContentPanelWidget(entity=entity)
        self.tabs.addTab(self.content_panel, "Контент")
        
        # History tab
        self.history_panel = HistoryPanelWidget(entity=entity)
        self.tabs.addTab(self.history_panel, "История")
        
        # Semantic Map tab
        self.semantic_map = SemanticMapWidget(entity=entity)
        self.tabs.addTab(self.semantic_map, "Карта смыслов")
        
        # Settings tab
        self.settings_panel = SettingsPanelWidget(entity=entity)
        self.tabs.addTab(self.settings_panel, "Настройки")
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Готов")
        
        # Update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_status)
        self.update_timer.start(5000)  # Update every 5 seconds
        
        # Initial status update (delayed)
        QTimer.singleShot(1000, self.update_status)
    
    def update_status(self):
        """Update status from entity."""
        if self.entity:
            try:
                status = self.entity.get_status()
                status_text = f"Статус: {status.get('status', 'unknown')}"
                if status.get('current_intent'):
                    status_text += f" | Намерение: {status['current_intent']}"
                self.status_bar.showMessage(status_text)
                
                # Emit signals for widgets
                self.signals.status_updated.emit(status)
                if 'metrics' in status:
                    self.signals.metrics_updated.emit(status['metrics'])
            except Exception as e:
                self.logger.error(f"Error updating status: {e}")
    
    def closeEvent(self, event):
        """Handle window close."""
        if self.entity and self.entity.running:
            # Stop entity gracefully
            import asyncio
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.create_task(self.entity.stop())
                else:
                    loop.run_until_complete(self.entity.stop())
            except Exception as e:
                self.logger.error(f"Error stopping entity: {e}")
        
        event.accept()


def run_ui(entity=None):
    """Run the UI application."""
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # Modern look
    
    window = MainWindow(entity=entity)
    window.show()
    
    sys.exit(app.exec())

