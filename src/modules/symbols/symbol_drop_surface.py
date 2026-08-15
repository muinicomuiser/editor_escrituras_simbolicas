from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QDropEvent, QPaintEvent, QPainter, QPixmap
from PIL import Image, ImageQt

class SymbolDropSurface(QWidget):
    image_dropped = Signal(str, bool)
    def __init__(self, parent=None, symbol_name: str = None):
        super().__init__(parent)
        self.symbol_name = symbol_name
        self.setAcceptDrops(True)
        self.pixmap = QPixmap()  

        self._valid_extensions = {".png", ".jpg", ".jpeg"}              
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

    # Evento de entrada de un elemento al área. De este evento depende dropEvent, porque le da una validación previa.
    def dragEnterEvent(self, event: QDropEvent):
        if not event.mimeData().hasUrls():
            event.ignore()
        if not (urls := event.mimeData().urls()):
            event.ignore()
        extension = Path(urls[0].toLocalFile()).suffix.lower()
        if not extension in self._valid_extensions:
            event.ignore()
        else:
            event.acceptProposedAction()
        return super().dragEnterEvent(event)        

    def has_symbol(self):
        return not self.pixmap.isNull()

    # Evento que se dispara cada vez que el mouse se mueve dentro del área, por cada pixel.
    # No es necesario para mi caso    
    # def dragMoveEvent(self, event: QDropEvent):
    #     event.accept()
    #     return super().dragMoveEvent(event)        

    def dropEvent(self, event: QDropEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            image_path = event.mimeData().urls()[0].toLocalFile()
            self.set_image(image_path, is_saved=False)
            event.accept()            

    def clear(self):
        self.pixmap = QPixmap()
        self.update()

    ## WIP
    def save_to_file(self, symbol_dir_path: Path):
        if not self.pixmap.isNull():      
            filename =  f"{self.symbol_name}{Path(self.image_path).suffix.lower()}"
            image_path = symbol_dir_path.joinpath(filename)
            saved = self.pixmap.save(str(image_path))
            if saved:
                self.image_path = image_path

    def set_image(self, image_path: str, is_saved: bool = False, drop: bool = True):

        pixmap = QPixmap(image_path)
        if not pixmap.isNull():
            if drop and pixmap.hasAlphaChannel():
                with Image.open(image_path) as image:
                    bounding_box = image.getbbox()
                    if bounding_box:
                        cropped = image.crop(bounding_box)
                        pixmap = ImageQt.toqpixmap(cropped)
            self.pixmap = pixmap
            self.image_path = str(image_path)
            self.image_dropped.emit(self.image_path, is_saved)
            self.update()
        

    def paintEvent(self, event: QPaintEvent):
        painter = QPainter(self)
            
        if not self.pixmap.isNull():
            scaled_pixmap = self.pixmap.scaled(self.size(), aspectMode=Qt.AspectRatioMode.KeepAspectRatio, mode=Qt.TransformationMode.SmoothTransformation)
            x = (self.width() - scaled_pixmap.width()) // 2
            y = (self.height() - scaled_pixmap.height()) // 2
            painter.drawPixmap(x, y, scaled_pixmap)
        painter.end()    
