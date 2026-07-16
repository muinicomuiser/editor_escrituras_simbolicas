import sys
from PySide6.QtWidgets import QApplication
from modules.main_window import MainWindow


def main():
    app = QApplication(sys.argv)

    main_window = MainWindow()
    main_window.setWindowTitle("Editor de Texto con Imágenes")
    main_window.resize(1024, 768)
    main_window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
