import signal
import sys
import os
from PySide6.QtWidgets import QApplication, QStyleFactory
from modules.config.config import load_config
from modules.main_window import MainWindow


def main():

    ### Anotación 1: Por refinar esta parte
    ## Forzar a usar un servidor gráfico específico (tengo problemas en linux al arrastrar imágenes)
    os.environ["QT_QPA_PLATFORM"] = "xcb"
    ### Fin Anotación 1

    
    app = QApplication(sys.argv)
    signal.signal(
        signal.SIGINT, signal.SIG_DFL
    )
    app.setStyle(QStyleFactory.create("Fusion")) 
    
    config = load_config()

    main_window = MainWindow(config)
    main_window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
