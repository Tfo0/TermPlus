from typing import List
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFileDialog, QDialogButtonBox, QComboBox,
    QRadioButton, QButtonGroup, QTableWidget, QTableWidgetItem,
    QHeaderView, QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt
from core.models import Profile


def _section_label(text: str) -> QLabel:
    lbl = QLabel(text)
    f = lbl.font()
    f.setBold(True)
    lbl.setFont(f)
    return lbl


class SettingsDialog(QDialog):
    def __init__(self, current_path: str, profiles: List[Profile],
                 current_default: str, current_theme: str,
                 presets: list, parent=None):
        super().__init__(parent)
        self.setWindowTitle("设置")
        self.setMinimumWidth(520)
        self.setMinimumHeight(500)
        self._init_ui(current_path, profiles, current_default,
                      current_theme, presets)

    def _init_ui(self, current_path, profiles, current_default,
                 current_theme, presets):
        layout = QVBoxLayout()
        layout.setSpacing(14)
        layout.setContentsMargins(20, 18, 20, 16)

        # ── 配置文件路径 ──────────────────────────────────────────────
        layout.addWidget(_section_label("配置文件路径"))
        path_row = QHBoxLayout()
        self.path_input = QLineEdit(current_path)
        browse_btn = QPushButton("浏览...")
        browse_btn.setFixedWidth(64)
        browse_btn.clicked.connect(self._browse)
        path_row.addWidget(self.path_input)
        path_row.addWidget(browse_btn)
        layout.addLayout(path_row)

        # ── 默认 Profile ──────────────────────────────────────────────
        layout.addWidget(_section_label("默认 Profile"))
        self.default_combo = QComboBox()
        for p in profiles:
            self.default_combo.addItem(p.name, p.guid)
        idx = next((i for i, p in enumerate(profiles) if p.guid == current_default), 0)
        self.default_combo.setCurrentIndex(idx)
        layout.addWidget(self.default_combo)

        # ── 界面主题 ──────────────────────────────────────────────────
        layout.addWidget(_section_label("界面主题"))
        theme_row = QHBoxLayout()
        self._theme_group = QButtonGroup(self)
        self._theme_radios: dict[str, QRadioButton] = {}
        for key, label in [("dark", "🌙  深色"), ("light", "☀  浅色")]:
            rb = QRadioButton(label)
            rb.setChecked(key == current_theme)
            self._theme_group.addButton(rb)
            theme_row.addWidget(rb)
            self._theme_radios[key] = rb
        theme_row.addStretch()
        layout.addLayout(theme_row)

        # ── 命令行预设 ──────────────────────────────────────────────
        layout.addWidget(_section_label("命令行预设"))

        self.preset_table = QTableWidget(0, 2)
        self.preset_table.setHorizontalHeaderLabels(["名称", "完整命令"])
        self.preset_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.ResizeToContents)
        self.preset_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch)
        self.preset_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows)
        self.preset_table.verticalHeader().setVisible(False)
        self.preset_table.setFixedHeight(150)

        for p in presets:
            self._add_preset_row(p.get("name", ""), p.get("command", ""))

        layout.addWidget(self.preset_table)

        preset_btn_row = QHBoxLayout()
        add_preset_btn = QPushButton("＋ 添加")
        del_preset_btn = QPushButton("－ 删除")
        add_preset_btn.setFixedWidth(70)
        del_preset_btn.setFixedWidth(70)
        add_preset_btn.clicked.connect(self._add_preset_row_empty)
        del_preset_btn.clicked.connect(self._del_preset_row)
        preset_btn_row.addWidget(add_preset_btn)
        preset_btn_row.addWidget(del_preset_btn)
        preset_btn_row.addStretch()
        layout.addLayout(preset_btn_row)

        # ── OK / Cancel ───────────────────────────────────────────────
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)

    # ── preset table helpers ──────────────────────────────────────────

    def _add_preset_row(self, name: str = "", command: str = ""):
        row = self.preset_table.rowCount()
        self.preset_table.insertRow(row)
        self.preset_table.setItem(row, 0, QTableWidgetItem(name))
        self.preset_table.setItem(row, 1, QTableWidgetItem(command))

    def _add_preset_row_empty(self):
        self._add_preset_row()
        self.preset_table.editItem(
            self.preset_table.item(self.preset_table.rowCount() - 1, 0))

    def _del_preset_row(self):
        row = self.preset_table.currentRow()
        if row >= 0:
            self.preset_table.removeRow(row)

    def _browse(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "选择 settings.json", "", "JSON Files (*.json)"
        )
        if path:
            self.path_input.setText(path)

    # ── getters ───────────────────────────────────────────────────────

    def get_path(self) -> str:
        return self.path_input.text()

    def get_default_profile(self) -> str:
        return self.default_combo.currentData() or ""

    def get_theme(self) -> str:
        return next((k for k, rb in self._theme_radios.items() if rb.isChecked()), "dark")

    def get_presets(self) -> list:
        result = []
        for row in range(self.preset_table.rowCount()):
            name_item = self.preset_table.item(row, 0)
            cmd_item = self.preset_table.item(row, 1)
            name = (name_item.text().strip() if name_item else "")
            cmd = (cmd_item.text().strip() if cmd_item else "")
            if name and cmd:
                result.append({"name": name, "command": cmd})
        return result
