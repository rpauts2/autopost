"""Platforms panel widget."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QGroupBox, QTextEdit,
    QComboBox, QDialog, QDialogButtonBox, QMessageBox
)
from PySide6.QtCore import Qt, QThread, Signal, QObject
from typing import Optional
import asyncio

from utils.logger import get_logger

logger = get_logger(__name__)


class AsyncWorker(QObject):
    """Async worker for platform operations."""
    finished = Signal(object)
    error = Signal(str)
    
    def __init__(self, coro):
        super().__init__()
        self.coro = coro
    
    def run(self):
        """Run async coroutine."""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self.coro)
            loop.close()
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class GroupSelectDialog(QDialog):
    """Dialog for selecting VK group."""
    
    def __init__(self, groups, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Выберите группу VK")
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout(self)
        
        layout.addWidget(QLabel("Доступные группы:"))
        
        self.group_combo = QComboBox()
        for group in groups:
            self.group_combo.addItem(group.get('name', f"Group {group.get('id')}"), group.get('id'))
        layout.addWidget(self.group_combo)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def get_selected_group_id(self):
        """Get selected group ID."""
        return self.group_combo.currentData()


class PlatformsPanelWidget(QWidget):
    """Widget for managing platform connections."""
    
    def __init__(self, entity=None):
        super().__init__()
        self.entity = entity
        self.logger = logger
        
        self._init_ui()
    
    def _init_ui(self):
        """Initialize UI."""
        layout = QVBoxLayout(self)
        
        # API Key section
        api_group = QGroupBox("Gemini API")
        api_layout = QVBoxLayout()
        
        api_layout.addWidget(QLabel("API Key:"))
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setEchoMode(QLineEdit.Password)
        api_layout.addWidget(self.api_key_edit)
        
        api_save_button = QPushButton("Сохранить API Key")
        api_save_button.clicked.connect(self.save_api_key)
        api_layout.addWidget(api_save_button)
        
        api_group.setLayout(api_layout)
        layout.addWidget(api_group)
        
        # VK section
        vk_group = QGroupBox("VK")
        vk_layout = QVBoxLayout()
        
        self.vk_status_label = QLabel("Не подключено")
        vk_layout.addWidget(self.vk_status_label)
        
        vk_layout.addWidget(QLabel("Access Token (из URL после авторизации):"))
        self.vk_token_edit = QLineEdit()
        self.vk_token_edit.setPlaceholderText("Вставьте access_token из URL")
        vk_layout.addWidget(self.vk_token_edit)
        
        vk_connect_button = QPushButton("Подключить VK")
        vk_connect_button.clicked.connect(self.connect_vk)
        vk_layout.addWidget(vk_connect_button)
        
        vk_group.setLayout(vk_layout)
        layout.addWidget(vk_group)
        
        # Telegram section
        tg_group = QGroupBox("Telegram")
        tg_layout = QVBoxLayout()
        
        self.tg_status_label = QLabel("Не подключено")
        tg_layout.addWidget(self.tg_status_label)
        
        tg_layout.addWidget(QLabel("Bot Token (от @BotFather):"))
        self.tg_token_edit = QLineEdit()
        self.tg_token_edit.setPlaceholderText("123456:ABC-DEF...")
        self.tg_token_edit.setEchoMode(QLineEdit.Password)
        tg_layout.addWidget(self.tg_token_edit)
        
        tg_layout.addWidget(QLabel("Chat ID (канал: @channel или -1001234567890):"))
        self.tg_chat_id_edit = QLineEdit()
        self.tg_chat_id_edit.setPlaceholderText("@my_channel или -1001234567890")
        tg_layout.addWidget(self.tg_chat_id_edit)
        
        tg_connect_button = QPushButton("Подключить Telegram")
        tg_connect_button.clicked.connect(self.connect_telegram)
        tg_layout.addWidget(tg_connect_button)
        
        tg_group.setLayout(tg_layout)
        layout.addWidget(tg_group)
        
        # Dzen section
        dzen_group = QGroupBox("Dzen")
        dzen_layout = QVBoxLayout()
        
        self.dzen_status_label = QLabel("Не подключено")
        dzen_layout.addWidget(self.dzen_status_label)
        
        dzen_layout.addWidget(QLabel("Авторизуйтесь в открывшемся браузере"))
        
        dzen_connect_button = QPushButton("Подключить Dzen")
        dzen_connect_button.clicked.connect(self.connect_dzen)
        dzen_layout.addWidget(dzen_connect_button)
        
        dzen_group.setLayout(dzen_layout)
        layout.addWidget(dzen_group)
        
        layout.addStretch()
        
        # Update status on init
        self.update_status()
    
    def save_api_key(self):
        """Save Gemini API key."""
        api_key = self.api_key_edit.text().strip()
        if not api_key:
            self.logger.warning("API key is empty")
            return
        
        try:
            if self.entity:
                self.entity.update_settings(gemini_api_key=api_key)
            else:
                from config.settings import update_settings
                update_settings(gemini_api_key=api_key)
            
            self.logger.info("API key saved")
        except Exception as e:
            self.logger.error(f"Error saving API key: {e}")
    
    def update_status(self):
        """Update platform statuses."""
        if not self.entity or not hasattr(self.entity, 'platform_manager'):
            return
        
        try:
            import threading
            
            def update():
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    statuses = loop.run_until_complete(self.entity.platform_manager.get_all_statuses())
                    loop.close()
                    
                    # Update UI using QTimer (thread-safe)
                    from PySide6.QtCore import QTimer
                    QTimer.singleShot(0, lambda: self._update_status_labels(statuses))
                except Exception as e:
                    self.logger.error(f"Error updating status in thread: {e}")
            
            thread = threading.Thread(target=update, daemon=True)
            thread.start()
        except Exception as e:
            self.logger.error(f"Error starting status update: {e}")
    
    def _update_status_labels(self, statuses):
        """Update status labels (called from main thread)."""
        try:
            # Update VK status
            vk_status = statuses.get('vk', {})
            if vk_status.get('authenticated'):
                group_id = vk_status.get('group_id')
                self.vk_status_label.setText(f"✅ Подключено" + (f" (группа: {group_id})" if group_id else ""))
            else:
                self.vk_status_label.setText("❌ Не подключено")
            
            # Update Telegram status
            tg_status = statuses.get('telegram', {})
            if tg_status.get('authenticated'):
                chat_id = tg_status.get('chat_id', '')
                bot_username = tg_status.get('bot_username', '')
                status_text = "✅ Подключено"
                if bot_username:
                    status_text += f" (@{bot_username}"
                    if chat_id:
                        status_text += f", chat: {chat_id}"
                    status_text += ")"
                self.tg_status_label.setText(status_text)
            else:
                self.tg_status_label.setText("❌ Не подключено")
            
            # Update Dzen status
            dzen_status = statuses.get('dzen', {})
            if dzen_status.get('authenticated'):
                self.dzen_status_label.setText("✅ Подключено")
            else:
                self.dzen_status_label.setText("❌ Не подключено")
        except Exception as e:
            self.logger.error(f"Error updating status labels: {e}")
    
    def connect_vk(self):
        """Connect VK platform."""
        token = self.vk_token_edit.text().strip()
        if not token:
            QMessageBox.warning(self, "Ошибка", "Введите VK Access Token")
            return
        
        if not self.entity or not hasattr(self.entity, 'platform_manager'):
            QMessageBox.warning(self, "Ошибка", "Entity не инициализирован")
            return
        
        try:
            platform = self.entity.platform_manager.get_platform("vk")
            if not platform:
                QMessageBox.warning(self, "Ошибка", "VK платформа не найдена")
                return
            
            # Authenticate
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Authenticate
            result = loop.run_until_complete(platform.authenticate({"access_token": token}))
            loop.close()
            
            if result:
                # Get groups
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                groups = loop.run_until_complete(platform.get_groups())
                loop.close()
                
                if groups:
                    # Show group selection dialog
                    dialog = GroupSelectDialog(groups, self)
                    if dialog.exec():
                        group_id = dialog.get_selected_group_id()
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        loop.run_until_complete(platform.select_group(group_id))
                        loop.close()
                        QMessageBox.information(self, "Успех", "VK подключен и группа выбрана")
                else:
                    QMessageBox.warning(self, "Предупреждение", "Нет доступных групп")
                
                self.update_status()
            else:
                QMessageBox.warning(self, "Ошибка", "Не удалось подключиться к VK")
        except Exception as e:
            self.logger.error(f"VK connection error: {e}")
            QMessageBox.critical(self, "Ошибка", f"Ошибка подключения: {str(e)}")
    
    def connect_telegram(self):
        """Connect Telegram platform."""
        token = self.tg_token_edit.text().strip()
        chat_id = self.tg_chat_id_edit.text().strip()
        
        if not token:
            QMessageBox.warning(self, "Ошибка", "Введите Bot Token")
            return
        
        if not self.entity or not hasattr(self.entity, 'platform_manager'):
            QMessageBox.warning(self, "Ошибка", "Entity не инициализирован")
            return
        
        try:
            platform = self.entity.platform_manager.get_platform("telegram")
            if not platform:
                QMessageBox.warning(self, "Ошибка", "Telegram платформа не найдена")
                return
            
            # Authenticate
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            result = loop.run_until_complete(platform.authenticate({"bot_token": token}))
            
            if result and chat_id:
                # Select chat
                select_result = loop.run_until_complete(platform.select_chat(chat_id))
                if not select_result:
                    QMessageBox.warning(self, "Предупреждение", "Бот не является администратором указанного чата")
            
            loop.close()
            
            if result:
                QMessageBox.information(self, "Успех", "Telegram подключен")
                self.update_status()
            else:
                QMessageBox.warning(self, "Ошибка", "Неверный Bot Token")
        except Exception as e:
            self.logger.error(f"Telegram connection error: {e}")
            QMessageBox.critical(self, "Ошибка", f"Ошибка подключения: {str(e)}")
    
    def connect_dzen(self):
        """Connect Dzen platform."""
        if not self.entity or not hasattr(self.entity, 'platform_manager'):
            QMessageBox.warning(self, "Ошибка", "Entity не инициализирован")
            return
        
        try:
            platform = self.entity.platform_manager.get_platform("dzen")
            if not platform:
                QMessageBox.warning(self, "Ошибка", "Dzen платформа не найдена")
                return
            
            QMessageBox.information(
                self,
                "Авторизация",
                "Откроется окно браузера. Пожалуйста, войдите в свой аккаунт Яндекс/Dzen."
            )
            
            # Authenticate (async)
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            result = loop.run_until_complete(platform.authenticate())
            loop.close()
            
            if result:
                QMessageBox.information(self, "Успех", "Dzen подключен")
                self.update_status()
            else:
                QMessageBox.warning(self, "Ошибка", "Не удалось подключиться к Dzen")
        except Exception as e:
            self.logger.error(f"Dzen connection error: {e}")
            QMessageBox.critical(self, "Ошибка", f"Ошибка подключения: {str(e)}")

