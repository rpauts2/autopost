from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel


class SemanticMapWidget(QWidget):
    def __init__(self, entity=None, parent=None):
        super().__init__(parent)
        self.entity = entity

        layout = QVBoxLayout(self)
        title = QLabel("Semantic Map")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")

        info = QLabel(
            "Semantic Map is not implemented yet.\n"
            "This widget will visualize topics, clusters and repetitions."
        )
        info.setStyleSheet("color: #777;")

        layout.addWidget(title)
        layout.addWidget(info)
        layout.addStretch()
