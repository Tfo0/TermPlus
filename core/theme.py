import platform
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QPalette, QColor


def apply_theme(app: QApplication, theme: str):
    if theme == "dark":
        _dark(app)
    elif theme == "light":
        _light(app)
    else:
        _system(app)


def _dark(app: QApplication):
    app.setStyle("Fusion")
    p = QPalette()
    p.setColor(QPalette.ColorRole.Window,          QColor(45, 45, 48))
    p.setColor(QPalette.ColorRole.WindowText,      QColor(240, 240, 240))
    p.setColor(QPalette.ColorRole.Base,            QColor(30, 30, 33))
    p.setColor(QPalette.ColorRole.AlternateBase,   QColor(45, 45, 48))
    p.setColor(QPalette.ColorRole.Text,            QColor(240, 240, 240))
    p.setColor(QPalette.ColorRole.Button,          QColor(55, 55, 58))
    p.setColor(QPalette.ColorRole.ButtonText,      QColor(240, 240, 240))
    p.setColor(QPalette.ColorRole.Link,            QColor(86, 156, 255))
    p.setColor(QPalette.ColorRole.Highlight,       QColor(0, 120, 215))
    p.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
    p.setColor(QPalette.ColorRole.Mid,             QColor(70, 70, 73))
    p.setColor(QPalette.ColorRole.Dark,            QColor(35, 35, 38))
    p.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text,       QColor(110, 110, 110))
    p.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, QColor(110, 110, 110))
    p.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, QColor(110, 110, 110))
    app.setPalette(p)


def _light(app: QApplication):
    app.setStyle("Fusion")
    p = QPalette()
    p.setColor(QPalette.ColorRole.Window,          QColor(240, 240, 240))
    p.setColor(QPalette.ColorRole.WindowText,      QColor(0, 0, 0))
    p.setColor(QPalette.ColorRole.Base,            QColor(255, 255, 255))
    p.setColor(QPalette.ColorRole.AlternateBase,   QColor(233, 233, 233))
    p.setColor(QPalette.ColorRole.Text,            QColor(0, 0, 0))
    p.setColor(QPalette.ColorRole.Button,          QColor(225, 225, 225))
    p.setColor(QPalette.ColorRole.ButtonText,      QColor(0, 0, 0))
    p.setColor(QPalette.ColorRole.Highlight,       QColor(0, 120, 215))
    p.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
    p.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text,       QColor(160, 160, 160))
    p.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, QColor(160, 160, 160))
    p.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, QColor(160, 160, 160))
    app.setPalette(p)


def _system(app: QApplication):
    if platform.system() == "Windows":
        app.setStyle("windowsvista")
    else:
        app.setStyle("Fusion")
    app.setPalette(app.style().standardPalette())
