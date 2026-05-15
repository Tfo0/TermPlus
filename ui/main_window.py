from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QMessageBox, QSplitter, QApplication
)
import sys
import os
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QIcon
from core.settings import SettingsManager
from core.app_config import AppConfig
from core.theme import apply_theme
from core.models import TerminalSettings
from .profile_list import ProfileListWidget
from .profile_form import ProfileForm
from .settings_dialog import SettingsDialog


class MainWindow(QMainWindow):
    def __init__(self, app_config: AppConfig = None):
        super().__init__()
        self.setWindowTitle("TermPlus  ·  by Tfo0")
        self.setGeometry(100, 100, 860, 500)
        _base = getattr(sys, '_MEIPASS', os.path.dirname(os.path.dirname(__file__)))
        self.setWindowIcon(QIcon(os.path.join(_base, 'assets', 'icon.ico')))

        self.app_config = app_config or AppConfig()
        self.settings_manager = SettingsManager(self.app_config.settings_json_path)
        self.current_settings: TerminalSettings = None
        self.modified = False

        self._init_ui()
        self.load_settings()

    def _init_ui(self):
        central = QWidget()
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(8, 6, 8, 6)
        main_layout.setSpacing(6)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        self.profile_list = ProfileListWidget()
        self.profile_form = ProfileForm(self.app_config.presets)

        self.profile_list.profile_selected.connect(self._on_profile_selected)
        self.profile_list.profile_added.connect(self.mark_modified)
        self.profile_list.profile_removed.connect(self.mark_modified)
        self.profile_form.live_update.connect(self._on_live_update)

        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(6)
        right_layout.addWidget(self.profile_form)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        for label, slot in [("保存", self.save_settings), ("重置", self.reset_settings)]:
            btn = QPushButton(label)
            btn.clicked.connect(slot)
            btn_layout.addWidget(btn)
        gear_btn = QPushButton("⚙  设置")
        gear_btn.clicked.connect(self._open_settings)
        btn_layout.addWidget(gear_btn)
        right_layout.addLayout(btn_layout)

        splitter.addWidget(self.profile_list)
        splitter.addWidget(right_widget)
        splitter.setSizes([180, 680])
        main_layout.addWidget(splitter)

        central.setLayout(main_layout)
        self.setCentralWidget(central)

    # ── settings dialog ───────────────────────────────────────────────────

    def _open_settings(self):
        active = [p for p in self.current_settings.profiles if not p.hidden] \
            if self.current_settings else []
        current_default = self.current_settings.defaultProfile \
            if self.current_settings else ""

        dialog = SettingsDialog(
            current_path=self.app_config.settings_json_path,
            profiles=active,
            current_default=current_default,
            current_theme=self.app_config.theme,
            presets=self.app_config.presets,
            parent=self,
        )
        if not dialog.exec():
            return

        new_path = dialog.get_path()
        new_default = dialog.get_default_profile()
        new_theme = dialog.get_theme()
        new_presets = dialog.get_presets()

        changed = False

        if new_path != self.app_config.settings_json_path:
            self.app_config.settings_json_path = new_path
            self.settings_manager = SettingsManager(new_path)
            self.load_settings()
            changed = True

        if self.current_settings and new_default != self.current_settings.defaultProfile:
            self.current_settings.defaultProfile = new_default
            self.mark_modified()

        if new_theme != self.app_config.theme:
            self.app_config.theme = new_theme
            apply_theme(QApplication.instance(), new_theme)
            changed = True

        if new_presets != self.app_config.presets:
            self.app_config.presets = new_presets
            self.profile_form.refresh_presets(new_presets)
            changed = True

        if changed or (self.current_settings and
                       new_default != self.current_settings.defaultProfile):
            self.app_config.save()

    # ── data loading ──────────────────────────────────────────────────────

    def load_settings(self):
        try:
            if not self.settings_manager.exists():
                QMessageBox.critical(
                    self, "错误",
                    f"找不到配置文件:\n{self.settings_manager.settings_path}\n\n"
                    "请点击右下角 ⚙ 设置正确的路径。"
                )
                return
            self.current_settings = self.settings_manager.load()
            self.profile_list.load_profiles(self.current_settings)
            self.modified = False
            self.setWindowTitle("TermPlus  ·  by Tfo0")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载配置失败: {e}")

    # ── slots ─────────────────────────────────────────────────────────────

    def _on_profile_selected(self, profile):
        self.profile_form.load_profile(profile)

    def _on_live_update(self):
        self.profile_list.refresh_list()
        self.mark_modified()

    def mark_modified(self):
        self.modified = True
        if not self.windowTitle().endswith(" *"):
            self.setWindowTitle(self.windowTitle() + " *")

    def save_settings(self):
        try:
            self.profile_form.get_profile()
            self.current_settings.profiles = self.profile_list.get_profiles_order()
            self.settings_manager.save(self.current_settings)
            self.modified = False
            self.setWindowTitle("TermPlus  ·  by Tfo0")
            QMessageBox.information(self, "成功", "配置已保存（原文件已备份为 .bak）")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存失败: {e}")

    def reset_settings(self):
        if QMessageBox.question(self, "确认", "确定要重置所有更改吗?") == \
                QMessageBox.StandardButton.Yes:
            self.load_settings()

    def closeEvent(self, event):
        if self.modified:
            reply = QMessageBox.question(
                self, "确认", "有未保存的更改，确定要关闭吗?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                event.ignore()
                return
        event.accept()
