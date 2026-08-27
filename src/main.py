import argparse
import signal
import sys
import os
import platform
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QStyleFactory
from modules.config.config import load_config
from modules.main_window import MainWindow
from style.stylesheet import stylesheet
from modules.utils.logger import get_logger, setup_logger


def main():


    parser = argparse.ArgumentParser(description="Editor de escrituras simbólicas")
    parser.add_argument(
        "-w", "--watch", help="ejecuta la aplicación con reload", action="store_true"
    )
    parser.add_argument(
        "--log-level", help="define el nivel de criticidad de los logs", default="info", const="info", nargs="?", choices=["debug", "info", "warn", "warning", "error", "critical", "fatal"]
    )
    args = parser.parse_args()

    config = load_config()
    setup_logger(
        level=args.log_level if args.log_level else "info",
        log_file=config.LOGS_FILEPATH
        )
    logger = get_logger("Escrituras Simbólicas")
    current_platform = platform.system()
    
    if current_platform == "Linux":
        # Forzar a usar un servidor gráfico específico (tengo problemas en linux al arrastrar imágenes)
        os.environ["QT_QPA_PLATFORM"] = "xcb"

    app = QApplication(sys.argv)
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    app.setStyle(QStyleFactory.create("Fusion"))
    app.setStyleSheet(stylesheet)

    main_window = MainWindow(config)


    # Para ejecutar en modo watch (con watchfile) usando la flag -w. Mueve la ventana a la pantalla en la posición segunda
    if args.watch:
        screens = app.screens()
        target_screen_index = 1
        if len(screens) > target_screen_index:
            screen_geo = screens[target_screen_index].geometry()
            main_window.move(screen_geo.topLeft())
            main_window.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
    logger.info('Aplicación Iniciada')
    main_window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
