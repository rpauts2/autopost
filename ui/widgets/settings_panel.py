from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel


class SettingsPanelWidget(QWidget):
    def __init__(self, entity=None, parent=None):
        super().__init__(parent)
        self.entity = entity

        layout = QVBoxLayout(self)
        title = QLabel("Settings")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")

        info = QLabel(
            "Global system settings will be here.\n"
            "Goals, limits, personality drift, autonomy level."
        )
        info.setStyleSheet("color: #777;")

        layout.addWidget(title)
        layout.addWidget(info)
        layout.addStretch()
