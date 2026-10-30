import uuid
import copy
from PyQt6.QtWidgets import (
    QApplication,
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem, QPushButton,
    QLabel, QAbstractItemView, QStyledItemDelegate, QStyle, QTreeWidget,
    QTreeWidgetItem, QMenu
)
from PyQt6.QtCore import pyqtSignal, Qt, QSize, QRect, QTimer
from PyQt6.QtGui import QColor, QPalette, QPixmap, QPainter, QFont, QIcon
from core.models import Profile, TerminalSettings, MenuFolder
from .folder_dialog import FolderDialog

_ROLE = Qt.ItemDataRole.UserRole


def _depth(index) -> int:
    depth = 0
    parent = index.parent()
    while parent.isValid():
        depth += 1
        parent = parent.parent()
    return depth


class ProfileItemDelegate(QStyledItemDelegate):
    """Paints profile rows: tabColor strip + icon + name. Used for both the
    menu tree and the archive list."""

    def paint(self, painter: QPainter, option, index):
        painter.save()
        rect = option.rect
        is_selected = bool(option.state & QStyle.StateFlag.State_Selected)

        if is_selected:
            painter.fillRect(rect, option.palette.color(QPalette.ColorRole.Highlight))
        else:
            painter.fillRect(rect, option.palette.color(QPalette.ColorRole.Base))

        payload = index.data(_ROLE)
        if not isinstance(payload, tuple):
            painter.restore()
            return
        kind, obj = payload

        x = rect.x() + 4
        pad = 6

        if kind == "profile":
            profile: Profile = obj
            if profile.tabColor:
                try:
                    painter.fillRect(QRect(x, rect.y() + 4, 4, rect.height() - 8), QColor(profile.tabColor))
                except Exception:
                    pass
            x += 4 + pad

            icon_size = 20
            if profile.icon and not profile.icon.startswith("ms-"):
                pixmap = QPixmap(profile.icon)
                if not pixmap.isNull():
                    pixmap = pixmap.scaled(icon_size, icon_size,
                                           Qt.AspectRatioMode.KeepAspectRatio,
                                           Qt.TransformationMode.SmoothTransformation)
                    iy = rect.y() + (rect.height() - icon_size) // 2
                    painter.drawPixmap(x, iy, pixmap)
                    x += icon_size + pad

            if is_selected:
                painter.setPen(option.palette.color(QPalette.ColorRole.HighlightedText))
            else:
                color = option.palette.color(QPalette.ColorRole.Text)
                if profile.hidden:
                    color.setAlpha(140)
                painter.setPen(color)

            text_rect = QRect(x, rect.y(), rect.right() - x - pad, rect.height())
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignVCenter, profile.name)

        elif kind == "folder":
            folder: MenuFolder = obj
            icon_size = 18
            painted_icon = False
            if folder.icon:
                pixmap = QPixmap(folder.icon)
                if not pixmap.isNull():
                    pixmap = pixmap.scaled(icon_size, icon_size,
                                           Qt.AspectRatioMode.KeepAspectRatio,
                                           Qt.TransformationMode.SmoothTransformation)
                    iy = rect.y() + (rect.height() - icon_size) // 2
                    painter.drawPixmap(x, iy, pixmap)
                    painted_icon = True
            if not painted_icon:
                if is_selected:
                    painter.setPen(option.palette.color(QPalette.ColorRole.HighlightedText))
                else:
                    painter.setPen(option.palette.color(QPalette.ColorRole.Text))
                glyph_font = QFont("Segoe MDL2 Assets")
                glyph_font.setPixelSize(11)
                painter.setFont(glyph_font)
                painter.drawText(QRect(x, rect.y(), icon_size, rect.height()),
                                 Qt.AlignmentFlag.AlignVCenter, "\ue8b7")
            x += icon_size + pad

            font = painter.font()
            font.setBold(True)
            painter.setFont(font)
            if is_selected:
                painter.setPen(option.palette.color(QPalette.ColorRole.HighlightedText))
            else:
                painter.setPen(option.palette.color(QPalette.ColorRole.Text))
            text_rect = QRect(x, rect.y(), rect.right() - x - pad, rect.height())
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignVCenter, folder.name)

        painter.restore()

    def sizeHint(self, option, index):
        return QSize(option.rect.width(), 32)


class MenuTreeWidget(QTreeWidget):
    """Tree of menu folders + ungrouped profiles with managed drag & drop."""

    structure_changed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setHeaderHidden(True)
        self.setDragDropMode(QAbstractItemView.DragDropMode.DragDrop)
        self.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setExpandsOnDoubleClick(False)
        self._press_folder = None
        self._press_pos = None

    def mousePressEvent(self, event):
        self._press_folder = None
        self._press_pos = None
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.position().toPoint()
            item = self.itemAt(pos)
            payload = item.data(0, _ROLE) if item is not None else None
            if payload and payload[0] == "folder":
                content_left = self.visualRect(self.indexFromItem(item)).left()
                if pos.x() >= content_left:
                    self._press_folder = item
                    self._press_pos = pos
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        if event.button() == Qt.MouseButton.LeftButton and self._press_folder is not None:
            pos = event.position().toPoint()
            item = self.itemAt(pos)
            if item is self._press_folder and \
                    (pos - self._press_pos).manhattanLength() < QApplication.startDragDistance():
                self._press_folder.setExpanded(not self._press_folder.isExpanded())
            self._press_folder = None
            self._press_pos = None

    def dropEvent(self, event):
        src_widget = event.source()
        if src_widget is not None and src_widget is not self:
            event.ignore()
            return
        dragged = self.currentItem()
        if dragged is None:
            event.ignore()
            return

        pos = event.position().toPoint()
        target = self.itemAt(pos)
        dragged_kind = dragged.data(0, _ROLE)[0]
        dragged_parent = dragged.parent()

        dest_parent = None
        index = self.topLevelItemCount()

        if target is not None and target is not dragged:
            target_kind = target.data(0, _ROLE)[0]
            rect = self.visualItemRect(target)
            rel = (pos.y() - rect.top()) / max(1, rect.height())
            if target_kind == "folder":
                if dragged_kind == "profile" and 0.25 <= rel <= 0.75:
                    dest_parent, index = target, target.childCount()
                elif rel < 0.5:
                    dest_parent, index = None, self.indexOfTopLevelItem(target)
                else:
                    dest_parent, index = None, self.indexOfTopLevelItem(target) + 1
            else:
                tparent = target.parent()
                tidx = (tparent.indexOfChild(target) if tparent
                        else self.indexOfTopLevelItem(target))
                if rel >= 0.5:
                    tidx += 1
                dest_parent, index = tparent, tidx
        elif target is dragged:
            event.ignore()
            return

        # Folders may not nest
        if dragged_kind == "folder" and dest_parent is not None:
            event.ignore()
            return

        # Target index was computed with dragged still present; adjust for removal
        if dragged_parent is dest_parent:
            old = (dragged_parent.indexOfChild(dragged) if dragged_parent
                   else self.indexOfTopLevelItem(dragged))
            if index > old:
                index -= 1

        # Detach
        if dragged_parent is not None:
            dragged_parent.takeChild(dragged_parent.indexOfChild(dragged))
        else:
            self.takeTopLevelItem(self.indexOfTopLevelItem(dragged))

        # Insert
        if dest_parent is not None:
            dest_parent.insertChild(index, dragged)
            dest_parent.setExpanded(True)
        else:
            self.insertTopLevelItem(index, dragged)

        # Leave the selection empty on purpose: after QDrag.exec() returns,
        # QAbstractItemView.startDrag removes the *selected* rows for an accepted
        # MoveAction (clearOrRemove). With an empty selection nothing is removed.
        # Re-select the moved item on the next event loop turn instead.
        self.clearSelection()
        event.setDropAction(Qt.DropAction.MoveAction)
        event.accept()
        QTimer.singleShot(0, lambda: self.setCurrentItem(dragged))
        self.structure_changed.emit()


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
    structure_changed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.settings: TerminalSettings = None
        self._tree_active = True
        self.init_ui()

    # ── UI ──────────────────────────────────────────────────────────────

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(2)
        layout.setContentsMargins(0, 0, 0, 0)

        self.menu_label = SectionLabel("菜单  (0)")
        layout.addWidget(self.menu_label)

        self.tree = MenuTreeWidget()
        self.tree.setMinimumHeight(100)
        self.tree.setItemDelegate(ProfileItemDelegate(self.tree))
        self.tree.itemSelectionChanged.connect(self._on_tree_selection)
        self.tree.itemDoubleClicked.connect(self._on_double_click)
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._on_tree_context_menu)
        self.tree.structure_changed.connect(self._on_structure_changed)
        layout.addWidget(self.tree, 3)

        self.archive_label = SectionLabel("归档  (0)")
        layout.addWidget(self.archive_label)

        self.archive_list = QListWidget()
        self.archive_list.setMinimumHeight(50)
        self.archive_list.setItemDelegate(ProfileItemDelegate(self.archive_list))
        self.archive_list.itemSelectionChanged.connect(self._on_archive_selection)
        layout.addWidget(self.archive_list, 1)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(4)

        mdl2_font = QFont("Segoe MDL2 Assets")
        mdl2_font.setPixelSize(13)

        self.add_btn = QPushButton("\ue710")
        self.folder_btn = QPushButton("\ue8f4")
        self.dup_btn = QPushButton("\ue8c8")
        self.del_btn = QPushButton("\ue74d")
        self.toggle_btn = QPushButton("\ue896")

        for btn in (self.add_btn, self.folder_btn, self.dup_btn,
                    self.del_btn, self.toggle_btn):
            btn.setFont(mdl2_font)
            btn.setFixedWidth(36)
        self.add_btn.setToolTip("新建 Profile(选中文件夹时直接建在里面)")
        self.folder_btn.setToolTip("新建文件夹(根目录)")
        self.dup_btn.setToolTip("复制选中的 Profile")
        self.del_btn.setToolTip("删除")
        self.toggle_btn.setToolTip("归档 / 恢复")

        self.add_btn.clicked.connect(self.add_profile)
        self.folder_btn.clicked.connect(self.add_folder)
        self.dup_btn.clicked.connect(self.duplicate_profile)
        self.del_btn.clicked.connect(self.delete_selected)
        self.toggle_btn.clicked.connect(self.toggle_archive)

        for btn in (self.add_btn, self.folder_btn, self.dup_btn, self.del_btn):
            btn_layout.addWidget(btn)
        btn_layout.addStretch()
        btn_layout.addWidget(self.toggle_btn)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

    # ── data loading ────────────────────────────────────────────────────

    def load_profiles(self, settings: TerminalSettings):
        self.settings = settings
        self.tree.clear()
        self.archive_list.clear()

        by_guid = {p.guid: p for p in settings.profiles}

        for folder in settings.menu_folders:
            folder_item = self._make_folder_item(folder)
            self.tree.addTopLevelItem(folder_item)
            for guid in folder.entries:
                profile = by_guid.get(guid)
                if profile and not profile.hidden:
                    folder_item.addChild(self._make_profile_item(profile))
            folder_item.setExpanded(True)

        in_folders = {guid for f in settings.menu_folders for guid in f.entries}
        loose_seen = set()
        for guid in settings.menu_loose:
            profile = by_guid.get(guid)
            if profile and not profile.hidden:
                self.tree.addTopLevelItem(self._make_profile_item(profile))
                loose_seen.add(guid)

        # Active profiles that are not referenced in the menu at all still show
        # via the remainingProfiles entry; display them at the root so they can
        # be dragged into folders.
        for profile in settings.profiles:
            if profile.hidden:
                self.archive_list.addItem(self._make_archive_item(profile))
            elif profile.guid not in in_folders and profile.guid not in loose_seen:
                self.tree.addTopLevelItem(self._make_profile_item(profile))

        self._update_labels()

    def _make_profile_item(self, profile: Profile) -> QTreeWidgetItem:
        item = QTreeWidgetItem()
        item.setData(0, _ROLE, ("profile", profile))
        item.setText(0, profile.name)
        return item

    def _make_folder_item(self, folder: MenuFolder) -> QTreeWidgetItem:
        item = QTreeWidgetItem()
        item.setData(0, _ROLE, ("folder", folder))
        item.setText(0, folder.name)
        item.setChildIndicatorPolicy(QTreeWidgetItem.ChildIndicatorPolicy.ShowIndicator)
        if folder.icon:
            icon = QIcon(folder.icon)
            if not icon.isNull():
                item.setIcon(0, icon)
        return item

    def _make_archive_item(self, profile: Profile) -> QListWidgetItem:
        item = QListWidgetItem()
        item.setData(_ROLE, ("profile", profile))
        item.setData(1000, profile.guid)
        return item

    def _update_labels(self):
        folders = 0
        profiles = 0
        for i in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(i)
            kind = item.data(0, _ROLE)[0]
            if kind == "folder":
                folders += 1
                profiles += item.childCount()
            else:
                profiles += 1
        self.menu_label.setText(f"菜单  ({folders} 个文件夹, {profiles} 个 Profile)")
        self.archive_label.setText(f"归档  ({self.archive_list.count()})")

    def refresh_list(self):
        self.tree.viewport().update()
        self.archive_list.viewport().update()

    # ── selection ───────────────────────────────────────────────────────

    def _on_tree_selection(self):
        self._tree_active = True
        self.archive_list.blockSignals(True)
        self.archive_list.clearSelection()
        self.archive_list.blockSignals(False)
        self.toggle_btn.setText("\ue896")
        self.toggle_btn.setToolTip("归档(从菜单中隐藏)")

        item = self.tree.currentItem()
        if item is None:
            return
        kind, obj = item.data(0, _ROLE)
        if kind == "profile":
            self.profile_selected.emit(obj)

    def _on_archive_selection(self):
        self._tree_active = False
        self.tree.blockSignals(True)
        self.tree.clearSelection()
        self.tree.blockSignals(False)
        self.toggle_btn.setText("\ue898")
        self.toggle_btn.setToolTip("恢复(重新显示在菜单中)")

        current = self.archive_list.currentItem()
        if current:
            kind, profile = current.data(_ROLE)
            if kind == "profile":
                self.profile_selected.emit(profile)

    def _on_double_click(self, item, _column):
        kind, obj = item.data(0, _ROLE)
        if kind != "folder":
            return
        dialog = FolderDialog(obj.name, obj.icon or "", self)
        if dialog.exec():
            name, icon = dialog.get_values()
            obj.name = name
            obj.icon = icon
            item.setText(0, name)
            item.setIcon(0, QIcon(icon) if icon else QIcon())
            self.structure_changed.emit()

    def _on_structure_changed(self):
        self._update_labels()
        self.structure_changed.emit()

    # ── context menu ────────────────────────────────────────────────────

    def _on_tree_context_menu(self, pos):
        item = self.tree.itemAt(pos)
        if item is None:
            return
        self.tree.setCurrentItem(item)
        kind, obj = item.data(0, _ROLE)

        menu = QMenu(self)
        if kind == "profile":
            move_menu = menu.addMenu("移动到")
            for i in range(self.tree.topLevelItemCount()):
                top = self.tree.topLevelItem(i)
                if top.data(0, _ROLE)[0] != "folder":
                    continue
                if item.parent() is top:
                    continue
                folder = top.data(0, _ROLE)[1]
                action = move_menu.addAction(folder.name)
                action.triggered.connect(
                    lambda checked=False, it=item, dest=top: self._move_item_to_folder(it, dest))
            if item.parent() is not None:
                root_action = move_menu.addAction("根目录(移出文件夹)")
                root_action.triggered.connect(
                    lambda checked=False, it=item: self._move_item_to_folder(it, None))
            menu.addSeparator()
            archive_action = menu.addAction("归档(从菜单隐藏)")
            archive_action.triggered.connect(self.toggle_archive)
        else:
            edit_action = menu.addAction("编辑文件夹…")
            edit_action.triggered.connect(
                lambda checked=False, it=item: self._on_double_click(it, 0))
            dissolve_action = menu.addAction("解散文件夹(子项移到根目录)")
            dissolve_action.triggered.connect(lambda checked=False: self.delete_selected())
        menu.exec(self.tree.viewport().mapToGlobal(pos))

    def _move_item_to_folder(self, item, folder_item):
        parent = item.parent()
        if parent is not None:
            parent.takeChild(parent.indexOfChild(item))
        else:
            self.tree.takeTopLevelItem(self.tree.indexOfTopLevelItem(item))
        if folder_item is not None:
            folder_item.addChild(item)
            folder_item.setExpanded(True)
        else:
            self.tree.addTopLevelItem(item)
        self.tree.setCurrentItem(item)
        self._on_structure_changed()

    # ── ordering / structure export ─────────────────────────────────────

    def get_profiles_order(self) -> list:
        result = []
        for i in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(i)
            kind, obj = item.data(0, _ROLE)
            if kind == "folder":
                for c in range(item.childCount()):
                    child_kind, profile = item.child(c).data(0, _ROLE)
                    if child_kind == "profile":
                        result.append(profile)
            else:
                result.append(obj)
        for i in range(self.archive_list.count()):
            kind, profile = self.archive_list.item(i).data(_ROLE)
            result.append(profile)
        return result

    def get_menu_structure(self):
        """Returns (folders, loose_guids) reflecting the current tree."""
        folders = []
        loose = []
        for i in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(i)
            kind, obj = item.data(0, _ROLE)
            if kind == "folder":
                folder = MenuFolder(
                    name=obj.name,
                    icon=obj.icon,
                    inlining=obj.inlining,
                    allow_empty=obj.allow_empty,
                )
                for c in range(item.childCount()):
                    child_kind, profile = item.child(c).data(0, _ROLE)
                    if child_kind == "profile":
                        folder.entries.append(profile.guid)
                folders.append(folder)
            else:
                loose.append(obj.guid)
        return folders, loose

    def get_active_profiles(self) -> list:
        return [p for p in self.settings.profiles if not p.hidden] if self.settings else []

    # ── add / delete / archive ──────────────────────────────────────────

    def add_profile(self):
        new_profile = Profile(
            guid="{" + str(uuid.uuid4()) + "}",
            name="新 Profile",
            commandline="cmd.exe"
        )
        self.settings.profiles.append(new_profile)
        item = self._make_profile_item(new_profile)

        current = self.tree.currentItem()
        if current is not None and current.data(0, _ROLE)[0] == "folder":
            current.addChild(item)
            current.setExpanded(True)
        elif current is not None and current.parent() is not None:
            folder_parent = current.parent()
            folder_parent.insertChild(folder_parent.indexOfChild(current) + 1, item)
        else:
            self.tree.addTopLevelItem(item)
        self.tree.setCurrentItem(item)
        self._on_structure_changed()
        self.profile_added.emit()

    def add_folder(self):
        dialog = FolderDialog(parent=self)
        if not dialog.exec():
            return
        name, icon = dialog.get_values()
        folder = MenuFolder(name=name, icon=icon)
        item = self._make_folder_item(folder)
        self.tree.addTopLevelItem(item)
        item.setExpanded(True)
        self.tree.setCurrentItem(item)
        self._on_structure_changed()

    def duplicate_profile(self):
        if self._tree_active:
            item = self.tree.currentItem()
            if item is None or item.data(0, _ROLE)[0] != "profile":
                return
            src: Profile = item.data(0, _ROLE)[1]
            new_profile = copy.deepcopy(src)
            new_profile.guid = "{" + str(uuid.uuid4()) + "}"
            new_profile.name = src.name + " (副本)"
            new_profile.hidden = False
            self.settings.profiles.append(new_profile)
            new_item = self._make_profile_item(new_profile)
            self.tree.addTopLevelItem(new_item)
            self.tree.setCurrentItem(new_item)
        else:
            current = self.archive_list.currentItem()
            if not current:
                return
            src: Profile = current.data(_ROLE)[1]
            new_profile = copy.deepcopy(src)
            new_profile.guid = "{" + str(uuid.uuid4()) + "}"
            new_profile.name = src.name + " (副本)"
            new_profile.hidden = False
            self.settings.profiles.append(new_profile)
            new_item = self._make_profile_item(new_profile)
            self.tree.addTopLevelItem(new_item)
            self.tree.setCurrentItem(new_item)
        self._on_structure_changed()
        self.profile_added.emit()

    def delete_selected(self):
        if self._tree_active:
            item = self.tree.currentItem()
            if item is None:
                return
            kind, obj = item.data(0, _ROLE)
            if kind == "profile":
                self.settings.profiles = [p for p in self.settings.profiles if p.guid != obj.guid]
                parent = item.parent()
                if parent is not None:
                    parent.takeChild(parent.indexOfChild(item))
                else:
                    self.tree.takeTopLevelItem(self.tree.indexOfTopLevelItem(item))
                self.profile_removed.emit()
            else:
                # delete folder: children become ungrouped at the folder's slot
                index = self.tree.indexOfTopLevelItem(item)
                children = item.takeChildren()
                self.tree.takeTopLevelItem(index)
                for offset, child in enumerate(children):
                    self.tree.insertTopLevelItem(index + offset, child)
            self._on_structure_changed()
        else:
            current = self.archive_list.currentItem()
            if not current:
                return
            guid = current.data(1000)
            self.settings.profiles = [p for p in self.settings.profiles if p.guid != guid]
            self.archive_list.takeItem(self.archive_list.row(current))
            self.profile_removed.emit()
            self._update_labels()

    def toggle_archive(self):
        if self._tree_active:
            item = self.tree.currentItem()
            if item is None or item.data(0, _ROLE)[0] != "profile":
                return
            profile: Profile = item.data(0, _ROLE)[1]
            profile.hidden = True
            parent = item.parent()
            if parent is not None:
                parent.takeChild(parent.indexOfChild(item))
            else:
                self.tree.takeTopLevelItem(self.tree.indexOfTopLevelItem(item))
            self.archive_list.addItem(self._make_archive_item(profile))
            self.archive_list.setCurrentRow(self.archive_list.count() - 1)
        else:
            current = self.archive_list.currentItem()
            if not current:
                return
            profile: Profile = current.data(_ROLE)[1]
            profile.hidden = False
            self.archive_list.takeItem(self.archive_list.row(current))
            item = self._make_profile_item(profile)
            self.tree.addTopLevelItem(item)
            self.tree.setCurrentItem(item)
        self._on_structure_changed()
