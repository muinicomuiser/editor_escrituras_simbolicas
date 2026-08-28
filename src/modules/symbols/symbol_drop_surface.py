from pathlib import Path

from PySide6.QtCore import QBuffer, QByteArray, QIODevice, Qt, Signal
from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QDropEvent, QPaintEvent, QPainter, QPixmap
from PIL import Image, ImageQt


class SymbolDropSurface(QWidget):
    image_dropped = Signal()

    def __init__(self, parent=None, symbol_name: str = None):
        super().__init__(parent)
        self.symbol_name = symbol_name
        self.setAcceptDrops(True)
        self.pixmap = QPixmap()

        self._valid_extensions = {".png", ".jpg", ".jpeg"}
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

    def get_symbol_name(self):
        return self.symbol_name

    def get_symbol_bytes(self):
        if self.pixmap.isNull():
            return None
        bytes_array = QByteArray()
        buffer = QBuffer(bytes_array)
        buffer.open(QIODevice.OpenModeFlag.WriteOnly)
        self.pixmap.save(buffer, "PNG") 
        buffer.close()
        return bytes_array
    
    def set_symbol_bytes(self, image_bytes: bytearray | bytes):
        """Recibe una imagen en bytes y la carga en el pixmap de esta superficie"""
        pixmap = QPixmap() 
        pixmap.loadFromData(image_bytes)     
        self.pixmap = pixmap
        self.update()

    def set_symbol(self, image_path: str, crop: bool = True):
        """Instancia un QPixmap a partir de una ruta de image y la fija en el Drop Surface. 
        El parámetro <crop: bool> permite decidir si se quiere recortar la sección vacía de una imagen con canal alfa."""
        pixmap = QPixmap(image_path)
        if not pixmap.isNull():
            if crop:
                pixmap = self._crop_image(pixmap)
            self.pixmap = pixmap
            self.image_path = str(image_path)
            self.update()

    def has_symbol(self):
        """Retorna True si la superficie tiene una imagen definida. De lo contrario, retorna False."""
        return not self.pixmap.isNull()

    def clear(self):
        """Asigna a la superficie un Pixmap vacío y la actualiza."""
        self.pixmap = QPixmap()
        self.update()
    
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

    def dropEvent(self, event: QDropEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            image_path = event.mimeData().urls()[0].toLocalFile()
            self.set_symbol(image_path)
            self.image_dropped.emit()
            event.accept()

    def paintEvent(self, _event: QPaintEvent):
        painter = QPainter(self)

        if not self.pixmap.isNull():
            scaled_pixmap = self.pixmap.scaled(
                self.size(),
                aspectMode=Qt.AspectRatioMode.KeepAspectRatio,
                mode=Qt.TransformationMode.SmoothTransformation,
            )
            x = (self.width() - scaled_pixmap.width()) // 2
            y = (self.height() - scaled_pixmap.height()) // 2
            painter.drawPixmap(x, y, scaled_pixmap)
        painter.end()

    def _crop_image(self, pixmap: QPixmap):
        if pixmap.hasAlphaChannel():
            image = Image.fromqpixmap(pixmap)
            bounding_box = image.getbbox()
            if bounding_box:
                cropped = image.crop(bounding_box)
                cropped_pixmap = ImageQt.toqpixmap(cropped)
                return cropped_pixmap
        return pixmap

    ## Por deprecar
    def get_file_name(self):
        return f"{self.symbol_name}{Path(self.image_path).suffix.lower()}"

    def get_format(self):
        """Retorna el formato de la imagen como str"""
        return Path(self.image_path).suffix.replace(".", "").upper()


    # def save_to_file(self, symbol_dir_path: Path) -> bool:
    #     """Guarda la imagen con el nombre del símbolo y la extensión de la imagen de origen en el directorio dado."""
    #     if self.pixmap and self.has_symbol():
    #         filename = f"{self.symbol_name}{Path(self.image_path).suffix.lower()}"
    #         image_path = symbol_dir_path.joinpath(filename)
    #         saved = self.pixmap.save(str(image_path))
    #         if saved:
    #             self.image_path = image_path
    #         return saved
    #     else:
    #         return False


