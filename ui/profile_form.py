from collections import OrderedDict
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QColorDialog,
    QPushButton, QFileDialog, QScrollArea, QFormLayout, QFrame, QLabel,
    QSizePolicy, QComboBox
)
from PyQt6.QtGui import QColor, QPainter, QPainterPath, QPen, QFont, QPixmap
from PyQt6.QtCore import pyqtSignal, Qt, QRect
from core.models import Profile


def _section_title(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
    f = lbl.font()
    f.setBold(True)
    f.setPointSize(10)
    lbl.setFont(f)
    return lbl


# ── Tab preview widget ─────────────────────────────────────────────────────────

class TabPreviewWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedHeight(48)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._name = ""
        self._color: str = None
        self._icon_path: str = None

    def update_preview(self, name: str, color: str = None, icon_path: str = None):
        self._name = name
        self._color = color
        self._icon_path = icon_path
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        tab_w = min(250, self.width() - 28)
        tab_h, y, r = 34, 7, 6
        x = (self.width() - tab_w) // 2

        path = QPainterPath()
        path.moveTo(x, y + tab_h)
        path.lineTo(x, y + r)
        path.quadTo(x, y, x + r, y)
        path.lineTo(x + tab_w - r, y)
        path.quadTo(x + tab_w, y, x + tab_w, y + r)
        path.lineTo(x + tab_w, y + tab_h)

        fill = QColor(self._color) if self._color else QColor(55, 55, 60)
        if self._color:
            fill.setAlpha(200)
        painter.fillPath(path, fill)
        painter.setPen(QPen(QColor(110, 110, 115), 1))
        painter.drawPath(path)

        cx = x + 10
        icon_size = 18
        if self._icon_path and not self._icon_path.startswith("ms-"):
            try:
                pix = QPixmap(self._icon_path)
                if not pix.isNull():
                    pix = pix.scaled(icon_size, icon_size,
                                     Qt.AspectRatioMode.KeepAspectRatio,
                                     Qt.TransformationMode.SmoothTransformation)
                    painter.drawPixmap(cx, y + (tab_h - icon_size) // 2, pix)
                    cx += icon_size + 6
            except Exception:
                pass

        painter.setPen(QColor(230, 230, 230))
        painter.setFont(QFont("Segoe UI", 9))
        painter.drawText(QRect(cx, y, tab_w - cx + x - 8, tab_h),
                         Qt.AlignmentFlag.AlignVCenter,
                         self._name or "未命名")
        painter.end()


# ── Main form widget ───────────────────────────────────────────────────────────

class ProfileForm(QWidget):
    live_update = pyqtSignal()

    def __init__(self, presets: list = None):
        super().__init__()
        self.current_profile: Profile = None
        self._tab_color: str = None
        self._presets: OrderedDict = OrderedDict()
        self._rebuild_presets(presets or [])
        self._init_ui()

    # ── preset management ─────────────────────────────────────────────

    def _rebuild_presets(self, presets: list):
        self._presets = OrderedDict()
        for p in presets:
            name = p.get("name", "").strip()
            cmd = p.get("command", "").strip()
            if name and cmd:
                self._presets[name] = cmd
        self._presets["自定义"] = ""

    def refresh_presets(self, presets: list):
        current_text = self.cmd_preset.currentText()
        self._rebuild_presets(presets)
        self.cmd_preset.blockSignals(True)
        self.cmd_preset.clear()
        for name in self._presets:
            self.cmd_preset.addItem(name)
        idx = self.cmd_preset.findText(current_text)
        self.cmd_preset.setCurrentIndex(max(0, idx))
        self.cmd_preset.blockSignals(False)

    def _is_custom(self) -> bool:
        return self.cmd_preset.currentText() == "自定义"

    def _full_command(self) -> str:
        user_text = self.cmd_user_input.text().strip()
        if self._is_custom():
            return user_text
        base = self._presets.get(self.cmd_preset.currentText(), "")
        return f"{base} {user_text}".strip() if user_text else base

    # ── UI construction ───────────────────────────────────────────────

    def _init_ui(self):
        outer = QVBoxLayout()
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(6)
        layout.setContentsMargins(16, 10, 16, 10)

        layout.addStretch(1)

        # ── 基本信息 ──────────────────────────────────────────────────
        layout.addWidget(_section_title("基本信息"))

        basic_wrap, basic_form = self._make_form()

        self.name_input = QLineEdit()
        self.name_input.textChanged.connect(self._on_name_changed)
        basic_form.addRow("名称:", self.name_input)

        self.tab_title_input = QLineEdit()
        basic_form.addRow("Tab 标题:", self.tab_title_input)

        cmd_row = QHBoxLayout()
        cmd_row.setSpacing(6)
        cmd_row.setContentsMargins(0, 0, 0, 0)

        self.cmd_preset = QComboBox()
        self.cmd_preset.setFixedWidth(100)
        for name in self._presets:
            self.cmd_preset.addItem(name)
        self.cmd_preset.currentTextChanged.connect(self._on_preset_changed)

        self.cmd_user_input = QLineEdit()
        self.cmd_user_input.setPlaceholderText("附加参数（可选）")
        self.cmd_user_input.textChanged.connect(self._on_user_input_changed)

        cmd_row.addWidget(self.cmd_preset)
        cmd_row.addWidget(self.cmd_user_input, 1)

        cmd_wrap = QWidget()
        cmd_wrap.setLayout(cmd_row)
        basic_form.addRow("命令行:", cmd_wrap)

        dir_row = QHBoxLayout()
        self.dir_input = QLineEdit()
        dir_btn = QPushButton("浏览...")
        dir_btn.setFixedWidth(58)
        dir_btn.clicked.connect(self._browse_dir)
        dir_row.addWidget(self.dir_input)
        dir_row.addWidget(dir_btn)
        basic_form.addRow("启动目录:", dir_row)

        layout.addWidget(basic_wrap)
        layout.addStretch(2)

        # ── Tab 外观 ──────────────────────────────────────────────────
        layout.addWidget(_section_title("Tab 外观"))

        appear_wrap, appear_form = self._make_form()

        icon_row = QHBoxLayout()
        self.icon_input = QLineEdit()
        self.icon_input.textChanged.connect(self._on_icon_changed)
        icon_btn = QPushButton("浏览...")
        icon_btn.setFixedWidth(58)
        icon_btn.clicked.connect(self._browse_icon)
        icon_row.addWidget(self.icon_input)
        icon_row.addWidget(icon_btn)
        appear_form.addRow("图标:", icon_row)

        color_row = QHBoxLayout()
        self.color_preview = QFrame()
        self.color_preview.setFixedSize(24, 24)
        self.color_preview.setFrameShape(QFrame.Shape.Box)
        self._set_preview_color(None)

        self.color_hex = QLineEdit()
        self.color_hex.setPlaceholderText("#RRGGBB")
        self.color_hex.setMaximumWidth(84)
        self.color_hex.textChanged.connect(self._on_color_text_changed)

        pick_btn = QPushButton("选色...")
        clear_btn = QPushButton("清除")
        pick_btn.setFixedWidth(56)
        clear_btn.setFixedWidth(46)
        pick_btn.clicked.connect(self._pick_color)
        clear_btn.clicked.connect(self._clear_color)

        color_row.addWidget(self.color_preview)
        color_row.addWidget(self.color_hex)
        color_row.addWidget(pick_btn)
        color_row.addWidget(clear_btn)
        color_row.addStretch()
        appear_form.addRow("Tab 颜色:", color_row)

        layout.addWidget(appear_wrap)
        layout.addStretch(2)

        # ── Tab 预览 ───────────────────────────────────────────────────
        layout.addWidget(_section_title("Tab 预览"))
        self.preview_widget = TabPreviewWidget()
        layout.addWidget(self.preview_widget)

        layout.addStretch(1)

        scroll.setWidget(container)
        outer.addWidget(scroll)
        self.setLayout(outer)

    def _make_form(self):
        w = QWidget()
        form = QFormLayout(w)
        form.setContentsMargins(0, 4, 0, 0)
        form.setVerticalSpacing(10)
        form.setHorizontalSpacing(12)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        return w, form

    # ── event handlers ────────────────────────────────────────────────

    def _on_name_changed(self, text):
        if self.current_profile:
            self.current_profile.name = text
            self._refresh_preview()
            self.live_update.emit()

    def _on_icon_changed(self, text):
        if self.current_profile:
            self.current_profile.icon = text or None
            self._refresh_preview()

    def _on_preset_changed(self, preset_name):
        is_custom = (preset_name == "自定义")
        self.cmd_user_input.setPlaceholderText("完整命令行" if is_custom else "附加参数（可选）")
        if self.current_profile:
            self.current_profile.commandline = self._full_command()

    def _on_user_input_changed(self, _):
        if self.current_profile:
            self.current_profile.commandline = self._full_command()

    def _on_color_text_changed(self, text):
        if len(text) == 7 and text.startswith("#"):
            try:
                c = QColor(text)
                if c.isValid():
                    self._tab_color = text.upper()
                    self._set_preview_color(c)
                    if self.current_profile:
                        self.current_profile.tabColor = self._tab_color
                        self._refresh_preview()
                        self.live_update.emit()
            except Exception:
                pass
        elif text == "":
            self._tab_color = None
            self._set_preview_color(None)
            if self.current_profile:
                self.current_profile.tabColor = None
                self._refresh_preview()
                self.live_update.emit()

    def _set_preview_color(self, color: QColor = None):
        if color and color.isValid():
            self.color_preview.setStyleSheet(
                f"background-color: {color.name()}; border: 1px solid #666;"
            )
        else:
            self.color_preview.setStyleSheet(
                "background-color: transparent; border: 1px solid #666;"
            )

    def _refresh_preview(self):
        if self.current_profile:
            self.preview_widget.update_preview(
                self.current_profile.name,
                self.current_profile.tabColor,
                self.current_profile.icon,
            )

    # ── public API ────────────────────────────────────────────────────

    def load_profile(self, profile: Profile):
        self.current_profile = profile

        for w in (self.name_input, self.color_hex, self.icon_input,
                  self.cmd_user_input, self.cmd_preset):
            w.blockSignals(True)

        self.name_input.setText(profile.name)
        self.tab_title_input.setText(profile.tabTitle or "")
        self.dir_input.setText(profile.startingDirectory)
        self.icon_input.setText(profile.icon or "")

        cmd = profile.commandline or ""
        matched_name = None
        for name, base in self._presets.items():
            if name == "自定义":
                continue
            if base and (cmd == base or cmd.startswith(base + " ")):
                matched_name = name
                self.cmd_preset.setCurrentText(name)
                self.cmd_user_input.setText(cmd[len(base):].strip())
                break

        if not matched_name:
            self.cmd_preset.setCurrentText("自定义")
            self.cmd_user_input.setText(cmd)

        self._tab_color = profile.tabColor
        self.color_hex.setText(profile.tabColor or "")
        self._set_preview_color(QColor(profile.tabColor) if profile.tabColor else None)

        for w in (self.name_input, self.color_hex, self.icon_input,
                  self.cmd_user_input, self.cmd_preset):
            w.blockSignals(False)

        self._on_preset_changed(self.cmd_preset.currentText())
        self._refresh_preview()

    def get_profile(self) -> Profile:
        if not self.current_profile:
            return None
        self.current_profile.name = self.name_input.text()
        self.current_profile.tabTitle = self.tab_title_input.text() or None
        self.current_profile.commandline = self._full_command()
        self.current_profile.startingDirectory = self.dir_input.text()
        self.current_profile.icon = self.icon_input.text() or None
        self.current_profile.tabColor = self._tab_color or None
        return self.current_profile

    # ── dialogs ───────────────────────────────────────────────────────

    def _browse_dir(self):
        path = QFileDialog.getExistingDirectory(self, "选择启动目录")
        if path:
            self.dir_input.setText(path)

    def _browse_icon(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "选择图标", "", "Image Files (*.png *.jpg *.ico);;All Files (*)"
        )
        if path:
            self.icon_input.setText(path)

    def _pick_color(self):
        initial = QColor(self._tab_color) if self._tab_color else QColor(255, 255, 255)
        color = QColorDialog.getColor(initial, self, "选择 Tab 颜色")
        if color.isValid():
            self._tab_color = color.name().upper()
            self.color_hex.blockSignals(True)
            self.color_hex.setText(self._tab_color)
            self.color_hex.blockSignals(False)
            self._set_preview_color(color)
            if self.current_profile:
                self.current_profile.tabColor = self._tab_color
                self._refresh_preview()
                self.live_update.emit()

    def _clear_color(self):
        self._tab_color = None
        self.color_hex.blockSignals(True)
        self.color_hex.setText("")
        self.color_hex.blockSignals(False)
        self._set_preview_color(None)
        if self.current_profile:
            self.current_profile.tabColor = None
            self._refresh_preview()
            self.live_update.emit()
