"""Settings panel with advanced options."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QSpinBox, QCheckBox,
    QGroupBox, QComboBox, QSlider, QDoubleSpinBox,
    QTextEdit
)
from PySide6.QtCore import Qt
from typing import Optional

from utils.logger import get_logger
from config.settings import get_settings, update_settings

logger = get_logger(__name__)


class SettingsPanelWidget(QWidget):
    """Widget for advanced settings."""
    
    def __init__(self, entity=None):
        super().__init__()
        self.entity = entity
        self.logger = logger
        self._init_ui()
        self.load_settings()
    
    def _init_ui(self):
        """Initialize UI."""
        layout = QVBoxLayout(self)
        
        # AI Settings
        ai_group = QGroupBox("Настройки AI")
        ai_layout = QVBoxLayout()
        
        ai_layout.addWidget(QLabel("Gemini API Key:"))
        self.gemini_key_edit = QLineEdit()
        self.gemini_key_edit.setEchoMode(QLineEdit.Password)
        ai_layout.addWidget(self.gemini_key_edit)
        
        ai_layout.addWidget(QLabel("Температура (creativity):"))
        self.temperature_slider = QSlider(Qt.Horizontal)
        self.temperature_slider.setMinimum(0)
        self.temperature_slider.setMaximum(100)
        self.temperature_slider.setValue(70)
        self.temperature_label = QLabel("0.7")
        temp_layout = QHBoxLayout()
        temp_layout.addWidget(self.temperature_slider)
        temp_layout.addWidget(self.temperature_label)
        self.temperature_slider.valueChanged.connect(
            lambda v: self.temperature_label.setText(f"{v/100:.2f}")
        )
        ai_layout.addLayout(temp_layout)
        
        ai_group.setLayout(ai_layout)
        layout.addWidget(ai_group)
        
        # Schedule Settings
        schedule_group = QGroupBox("Настройки расписания")
        schedule_layout = QVBoxLayout()
        
        schedule_layout.addWidget(QLabel("Интервал генерации (часы):"))
        self.interval_spin = QSpinBox()
        self.interval_spin.setMinimum(1)
        self.interval_spin.setMaximum(168)
        self.interval_spin.setValue(1)
        schedule_layout.addWidget(self.interval_spin)
        
        self.auto_start_check = QCheckBox("Автозапуск при старте")
        schedule_layout.addWidget(self.auto_start_check)
        
        schedule_layout.addWidget(QLabel("Ночной режим (с до):"))
        night_layout = QHBoxLayout()
        self.night_start = QSpinBox()
        self.night_start.setMinimum(0)
        self.night_start.setMaximum(23)
        self.night_start.setValue(22)
        self.night_end = QSpinBox()
        self.night_end.setMinimum(0)
        self.night_end.setMaximum(23)
        self.night_end.setValue(8)
        night_layout.addWidget(self.night_start)
        night_layout.addWidget(QLabel("до"))
        night_layout.addWidget(self.night_end)
        schedule_layout.addLayout(night_layout)
        
        self.night_mode_check = QCheckBox("Включить ночной режим")
        schedule_layout.addWidget(self.night_mode_check)
        
        schedule_group.setLayout(schedule_layout)
        layout.addWidget(schedule_group)
        
        # Content Settings
        content_group = QGroupBox("Настройки контента")
        content_layout = QVBoxLayout()
        
        content_layout.addWidget(QLabel("Минимальное качество контента:"))
        self.min_quality_spin = QDoubleSpinBox()
        self.min_quality_spin.setMinimum(0.0)
        self.min_quality_spin.setMaximum(1.0)
        self.min_quality_spin.setSingleStep(0.1)
        self.min_quality_spin.setValue(0.7)
        content_layout.addWidget(self.min_quality_spin)
        
        self.banality_filter_check = QCheckBox("Включить фильтр банальности")
        self.banality_filter_check.setChecked(True)
        content_layout.addWidget(self.banality_filter_check)
        
        self.density_check_check = QCheckBox("Проверка смысловой плотности")
        self.density_check_check.setChecked(True)
        content_layout.addWidget(self.density_check_check)
        
        content_layout.addWidget(QLabel("Порог плотности:"))
        self.density_threshold_spin = QDoubleSpinBox()
        self.density_threshold_spin.setMinimum(0.0)
        self.density_threshold_spin.setMaximum(1.0)
        self.density_threshold_spin.setSingleStep(0.05)
        self.density_threshold_spin.setValue(0.3)
        content_layout.addWidget(self.density_threshold_spin)
        
        content_group.setLayout(content_layout)
        layout.addWidget(content_group)
        
        # Image Settings
        image_group = QGroupBox("Настройки изображений")
        image_layout = QVBoxLayout()
        
        self.image_gen_check = QCheckBox("Генерировать изображения")
        self.image_gen_check.setChecked(True)
        image_layout.addWidget(self.image_gen_check)
        
        image_layout.addWidget(QLabel("Стиль изображений:"))
        self.image_style_combo = QComboBox()
        self.image_style_combo.addItems(["realistic", "artistic", "minimalist", "vibrant", "dark"])
        image_layout.addWidget(self.image_style_combo)
        
        image_group.setLayout(image_layout)
        layout.addWidget(image_group)
        
        # Save button
        save_button = QPushButton("Сохранить настройки")
        save_button.clicked.connect(self.save_settings)
        layout.addWidget(save_button)
        
        layout.addStretch()
    
    def load_settings(self):
        """Load settings from entity or config."""
        try:
            settings = get_settings()
            
            if settings.gemini_api_key:
                self.gemini_key_edit.setText(settings.gemini_api_key)
            
            self.auto_start_check.setChecked(settings.auto_start)
            # Load other settings...
            
        except Exception as e:
            self.logger.error(f"Error loading settings: {e}")
    
    def save_settings(self):
        """Save settings."""
        try:
            settings = get_settings()
            
            # Update API key
            api_key = self.gemini_key_edit.text().strip()
            if api_key:
                settings.gemini_api_key = api_key
                if self.entity and hasattr(self.entity, 'ai_client'):
                    self.entity.ai_client.configure(api_key)
            
            # Update other settings
            settings.auto_start = self.auto_start_check.isChecked()
            
            # Save
            update_settings(settings)
            
            # Update entity if available
            if self.entity:
                self.entity.settings = settings
            
            self.logger.info("Settings saved")
            # Show success message
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.information(self, "Настройки", "Настройки сохранены!")
            
        except Exception as e:
            self.logger.error(f"Error saving settings: {e}")
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Ошибка", f"Ошибка сохранения: {e}")

