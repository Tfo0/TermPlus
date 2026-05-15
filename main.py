import sys
from PyQt6.QtWidgets import QApplication
from core.app_config import AppConfig
from core.theme import apply_theme
from ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)

    config = AppConfig()
    apply_theme(app, config.theme)

    window = MainWindow(app_config=config)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
