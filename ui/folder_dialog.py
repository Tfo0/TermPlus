from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QPushButton,
    QFileDialog, QHBoxLayout, QDialogButtonBox, QLabel
)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt


class FolderDialog(QDialog):
    """Create or edit a newTabMenu folder: name + optional icon."""

    def __init__(self, name: str = "", icon: str = "", parent=None):
        super().__init__(parent)
        self.setWindowTitle("文件夹")
        self.setMinimumWidth(380)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.name_edit = QLineEdit(name)
        self.name_edit.setPlaceholderText("例如: Claude / Codex / as")
        form_row = QHBoxLayout()
        form_row.addWidget(self.name_edit)
        form.addRow("名称", form_row)

        icon_row = QHBoxLayout()
        self.icon_edit = QLineEdit(icon or "")
        self.icon_edit.setPlaceholderText("留空则使用默认文件夹图标")
        browse_btn = QPushButton("浏览…")
        browse_btn.clicked.connect(self._browse_icon)
        icon_row.addWidget(self.icon_edit)
        icon_row.addWidget(browse_btn)
        form.addRow("图标", icon_row)

        self.icon_preview = QLabel()
        self.icon_preview.setFixedSize(40, 40)
        self.icon_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._update_preview(icon or "")
        self.icon_edit.textChanged.connect(self._update_preview)
        form.addRow("", self.icon_preview)

        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _browse_icon(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "选择图标", "", "图片 (*.png *.ico *.jpg *.jpeg *.bmp);;所有文件 (*)"
        )
        if path:
            self.icon_edit.setText(path.replace("\\", "/"))

    def _update_preview(self, path: str):
        pixmap = QPixmap(path) if path else QPixmap()
        if pixmap.isNull():
            self.icon_preview.setText("无")
            self.icon_preview.setPixmap(QPixmap())
        else:
            self.icon_preview.setText("")
            self.icon_preview.setPixmap(
                pixmap.scaled(32, 32, Qt.AspectRatioMode.KeepAspectRatio,
                              Qt.TransformationMode.SmoothTransformation)
            )

    def accept(self):
        if not self.name_edit.text().strip():
            self.name_edit.setFocus()
            return
        super().accept()

    def get_values(self):
        icon = self.icon_edit.text().strip() or None
        return self.name_edit.text().strip(), icon
