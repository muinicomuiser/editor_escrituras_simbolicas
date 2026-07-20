import sys
from PySide6.QtWidgets import QApplication
from modules.config.config import load_config
from modules.main_window import MainWindow


def main():
    app = QApplication(sys.argv)

    config = load_config()

    main_window = MainWindow(config)
    # main_window.setWindowTitle("Editor de Texto con Imágenes")
    # main_window.resize(1024, 768)
    main_window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
