import argparse
import signal
import sys
import os
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QStyleFactory
from modules.config.config import load_config
from modules.main_window import MainWindow
from style.stylesheet import stylesheet


def main():

    ### Anotación 1: Por refinar esta parte
    ## Forzar a usar un servidor gráfico específico (tengo problemas en linux al arrastrar imágenes)
    #  os.environ["QT_QPA_PLATFORM"] = "xcb"
    ### Fin Anotación 1

    app = QApplication(sys.argv)
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    app.setStyle(QStyleFactory.create("Fusion"))
    app.setStyleSheet(stylesheet)

    config = load_config()

    main_window = MainWindow(config)

    parser = argparse.ArgumentParser(description="Editor de escrituras simbólicas")
    parser.add_argument(
        "-w", "--watch", help="ejecuta la aplicación con reload", action="store_true"
    )
    args = parser.parse_args()

    # Para ejecutar en modo watch (con watchfile) usando la flag -w. Mueve la ventana a la pantalla en la posición segunda
    if args.dev:
        screens = app.screens()
        target_screen_index = 1
        if len(screens) > target_screen_index:
            screen_geo = screens[target_screen_index].geometry()
            main_window.move(screen_geo.topLeft())
            main_window.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
    main_window.show()
    # main_window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
