import uuid
import copy
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem, QPushButton,
    QLabel, QAbstractItemView, QStyledItemDelegate, QStyle
)
from PyQt6.QtCore import pyqtSignal, Qt, QSize, QRect
from PyQt6.QtGui import QColor, QPalette, QPixmap, QPainter, QFont
from core.models import Profile, TerminalSettings


class ProfileItemDelegate(QStyledItemDelegate):
    def paint(self, painter: QPainter, option, index):
        painter.save()
        rect = option.rect
        is_selected = bool(option.state & QStyle.StateFlag.State_Selected)

        if is_selected:
            painter.fillRect(rect, option.palette.color(QPalette.ColorRole.Highlight))
        else:
            painter.fillRect(rect, option.palette.color(QPalette.ColorRole.Base))

        profile: Profile = index.data(Qt.ItemDataRole.UserRole)
        if not profile:
            painter.restore()
            return

        x = rect.x()
        pad = 6

        if profile.tabColor:
            try:
                painter.fillRect(QRect(x, rect.y(), 4, rect.height()), QColor(profile.tabColor))
            except Exception:
                pass
        x += 4 + pad

        icon_size = 20
        if profile.icon and not profile.icon.startswith("ms-"):
            try:
                pixmap = QPixmap(profile.icon)
                if not pixmap.isNull():
                    pixmap = pixmap.scaled(icon_size, icon_size,
                                           Qt.AspectRatioMode.KeepAspectRatio,
                                           Qt.TransformationMode.SmoothTransformation)
                    iy = rect.y() + (rect.height() - icon_size) // 2
                    painter.drawPixmap(x, iy, pixmap)
                    x += icon_size + pad
            except Exception:
                pass

        if is_selected:
            painter.setPen(option.palette.color(QPalette.ColorRole.HighlightedText))
        else:
            color = option.palette.color(QPalette.ColorRole.Text)
            if profile.hidden:
                color.setAlpha(140)
            painter.setPen(color)

        text_rect = QRect(x, rect.y(), rect.right() - x - pad, rect.height())
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignVCenter, profile.name)
        painter.restore()

    def sizeHint(self, option, index):
        return QSize(option.rect.width(), 36)


class SectionLabel(QLabel):
    def __init__(self, text):
        super().__init__(text)
        font = QFont()
        font.setBold(True)
        font.setPointSize(9)
        self.setFont(font)
        self.setStyleSheet("color: #888; padding: 4px 6px 2px 6px;")


class ProfileListWidget(QWidget):
    profile_selected = pyqtSignal(Profile)
    profile_added = pyqtSignal()
    profile_removed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.settings: TerminalSettings = None
        self._active_selected = True
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(2)
        layout.setContentsMargins(0, 0, 0, 0)

        # --- 常用 section ---
        self.active_label = SectionLabel("常用  (0)")
        layout.addWidget(self.active_label)

        self.active_list = QListWidget()
        self.active_list.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.active_list.setItemDelegate(ProfileItemDelegate(self.active_list))
        self.active_list.itemSelectionChanged.connect(
            lambda: self._on_selection(self.active_list)
        )
        layout.addWidget(self.active_list, 3)

        # --- 归档 section ---
        self.archive_label = SectionLabel("归档  (0)")
        layout.addWidget(self.archive_label)

        self.archive_list = QListWidget()
        self.archive_list.setItemDelegate(ProfileItemDelegate(self.archive_list))
        self.archive_list.itemSelectionChanged.connect(
            lambda: self._on_selection(self.archive_list)
        )
        layout.addWidget(self.archive_list, 1)

        # --- Buttons ---
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(4)

        self.up_btn = QPushButton("↑")
        self.down_btn = QPushButton("↓")
        self.add_btn = QPushButton("+")
        self.dup_btn = QPushButton("⧉")
        self.del_btn = QPushButton("−")
        self.toggle_btn = QPushButton("→ 归档")

        for btn in (self.up_btn, self.down_btn, self.add_btn, self.dup_btn, self.del_btn):
            btn.setFixedWidth(32)
        self.dup_btn.setToolTip("复制选中的 Profile")
        self.toggle_btn.setMinimumWidth(60)

        self.up_btn.clicked.connect(self.move_up)
        self.down_btn.clicked.connect(self.move_down)
        self.add_btn.clicked.connect(self.add_profile)
        self.dup_btn.clicked.connect(self.duplicate_profile)
        self.del_btn.clicked.connect(self.delete_profile)
        self.toggle_btn.clicked.connect(self.toggle_archive)

        btn_layout.addWidget(self.up_btn)
        btn_layout.addWidget(self.down_btn)
        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.dup_btn)
        btn_layout.addWidget(self.del_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(self.toggle_btn)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

    # ── data loading ──────────────────────────────────────────────────────

    def load_profiles(self, settings: TerminalSettings):
        self.settings = settings
        self.active_list.clear()
        self.archive_list.clear()
        for profile in settings.profiles:
            item = self._make_item(profile)
            if profile.hidden:
                self.archive_list.addItem(item)
            else:
                self.active_list.addItem(item)
        self._update_labels()

    def _make_item(self, profile: Profile) -> QListWidgetItem:
        item = QListWidgetItem()
        item.setData(Qt.ItemDataRole.UserRole, profile)
        item.setData(1000, profile.guid)
        return item

    def _update_labels(self):
        self.active_label.setText(f"常用  ({self.active_list.count()})")
        self.archive_label.setText(f"归档  ({self.archive_list.count()})")

    def refresh_list(self):
        self.active_list.viewport().update()
        self.archive_list.viewport().update()

    # ── selection ─────────────────────────────────────────────────────────

    def _on_selection(self, source: QListWidget):
        other = self.archive_list if source is self.active_list else self.active_list
        other.blockSignals(True)
        other.clearSelection()
        other.blockSignals(False)

        self._active_selected = (source is self.active_list)
        self.toggle_btn.setText("→ 归档" if self._active_selected else "← 常用")
        self.up_btn.setEnabled(self._active_selected)
        self.down_btn.setEnabled(self._active_selected)

        current = source.currentItem()
        if current:
            profile: Profile = current.data(Qt.ItemDataRole.UserRole)
            if profile:
                self.profile_selected.emit(profile)

    # ── ordering ──────────────────────────────────────────────────────────

    def get_profiles_order(self) -> list:
        result = []
        for lst in (self.active_list, self.archive_list):
            for i in range(lst.count()):
                p = lst.item(i).data(Qt.ItemDataRole.UserRole)
                if p:
                    result.append(p)
        return result

    def get_active_profiles(self) -> list:
        return [
            self.active_list.item(i).data(Qt.ItemDataRole.UserRole)
            for i in range(self.active_list.count())
        ]

    def move_up(self):
        row = self.active_list.currentRow()
        if row <= 0:
            return
        item = self.active_list.takeItem(row)
        self.active_list.insertItem(row - 1, item)
        self.active_list.setCurrentRow(row - 1)

    def move_down(self):
        row = self.active_list.currentRow()
        if row < 0 or row >= self.active_list.count() - 1:
            return
        item = self.active_list.takeItem(row)
        self.active_list.insertItem(row + 1, item)
        self.active_list.setCurrentRow(row + 1)

    # ── archive toggle ────────────────────────────────────────────────────

    def toggle_archive(self):
        if self._active_selected and self.active_list.currentItem():
            row = self.active_list.currentRow()
            item = self.active_list.takeItem(row)
            profile: Profile = item.data(Qt.ItemDataRole.UserRole)
            profile.hidden = True
            self.archive_list.addItem(item)
            self.archive_list.setCurrentItem(item)
        elif not self._active_selected and self.archive_list.currentItem():
            row = self.archive_list.currentRow()
            item = self.archive_list.takeItem(row)
            profile: Profile = item.data(Qt.ItemDataRole.UserRole)
            profile.hidden = False
            self.active_list.addItem(item)
            self.active_list.setCurrentItem(item)
        self._update_labels()

    # ── add / delete ──────────────────────────────────────────────────────

    def add_profile(self):
        new_profile = Profile(
            guid="{" + str(uuid.uuid4()) + "}",
            name="新 Profile",
            commandline="cmd.exe"
        )
        self.settings.profiles.append(new_profile)
        item = self._make_item(new_profile)
        self.active_list.addItem(item)
        self.active_list.setCurrentItem(item)
        self._update_labels()
        self.profile_added.emit()

    def duplicate_profile(self):
        lst = self.active_list if self._active_selected else self.archive_list
        current = lst.currentItem()
        if not current:
            return
        src: Profile = current.data(Qt.ItemDataRole.UserRole)
        new_profile = copy.deepcopy(src)
        new_profile.guid = "{" + str(uuid.uuid4()) + "}"
        new_profile.name = src.name + " (副本)"
        new_profile.hidden = False
        self.settings.profiles.append(new_profile)
        item = self._make_item(new_profile)
        self.active_list.addItem(item)
        self.active_list.setCurrentItem(item)
        self._update_labels()
        self.profile_added.emit()

    def delete_profile(self):
        lst = self.active_list if self._active_selected else self.archive_list
        current = lst.currentItem()
        if not current:
            return
        guid = current.data(1000)
        self.settings.profiles = [p for p in self.settings.profiles if p.guid != guid]
        lst.takeItem(lst.row(current))
        self._update_labels()
        self.profile_removed.emit()
