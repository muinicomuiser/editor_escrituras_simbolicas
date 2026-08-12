from itertools import chain
from PySide6.QtCore import QEvent, QObject, QSize, Qt
from PySide6.QtWidgets import QGridLayout, QLabel, QMainWindow, QScrollArea, QSizePolicy, QVBoxLayout, QWidget
from PySide6.QtGui import QDropEvent, QPaintEvent, QPainter, QPixmap


class SymbolSelectorWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._drop_container_object_name = "DropSymbolWidget"
        self._drop_container_surface_object_name = "DropSymbolSurface"

        self.setAcceptDrops(True)
        self.setWindowTitle("Editor de colección de símbolos")
        self.base_size = QSize(720, 480)
        self.resize(self.base_size)
        self.setMinimumSize(self.base_size)
        container = QWidget()
        layout = QGridLayout(container)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(container)
        self.setCentralWidget(scroll)
        self.characters = {
            "single": list("abcdefghijklmnñopqrstuvwxyz"),
            "compound": ["ch", "ll"]
        }



        for idx, character in enumerate(chain.from_iterable(self.characters.values())):
            drop_container = QWidget()
            drop_container.setObjectName(self._drop_container_object_name)
            drop_layout = QVBoxLayout(drop_container)
            drop_surface = DropSymbolWidget(symbol_name=character)
            drop_surface.setObjectName(self._drop_container_surface_object_name)
            drop_label = QLabel(character)
            drop_label.setMaximumHeight(drop_label.fontMetrics().height())
            drop_surface.installEventFilter(self)
            drop_layout.addWidget(drop_label)
            drop_layout.addWidget(drop_surface)
            drop_container.setFixedSize(QSize(160, 160))
            row, col = idx // 4, idx % 4
            layout.addWidget(drop_container, row, col)

        # style
                
        self.setStyleSheet("""
            #DropSymbolWidget {
                border: 2px solid #888888;
            }
            #DropSymbolSurface {
                border: 2px solid #444444;
                background-color: #ffffff;
            }
        """)

    def eventFilter(self, watched: QObject, event: QEvent):
        if event.type() == QEvent.Type.Drop:
            if event.mimeData().hasUrls():
                event.acceptProposedAction()
                image_path = event.mimeData().urls()[0].path()
                print(image_path)
                print(watched.symbol_name)
                watched.paint_image(image_path)
                return True
        return super().eventFilter(watched, event)
    
    def closeEvent(self, event):
        self.deleteLater()
        event.accept()    



class DropSymbolWidget(QWidget):
    def __init__(self, parent=None, symbol_name = None):
        super().__init__(parent)
        self.symbol_name = symbol_name
        self.setAcceptDrops(True)
        self.pixmap = QPixmap()        

        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

 
        
        # self.setObjectName("DropSymbolWidget")
        # self.setStyleSheet("""
        #     #DropSymbolWidget {
        #         border: 2px solid #444444;
        #         background-color: #ffffff;
        #     }
        # """)
    def dragEnterEvent(self, event: QDropEvent):
        event.accept()
        return super().dragEnterEvent(event)        
    def dragMoveEvent(self, event: QDropEvent):
        event.accept()
        return super().dragMoveEvent(event)        

    def paint_image(self, image_path: str):
        self.pixmap = QPixmap(image_path)
        if not self.pixmap.isNull():
            self.update()

    def paintEvent(self, event: QPaintEvent):
        painter = QPainter(self)
            
        if not self.pixmap.isNull():
            painter.drawPixmap(self.rect(), self.pixmap)
        painter.end()    