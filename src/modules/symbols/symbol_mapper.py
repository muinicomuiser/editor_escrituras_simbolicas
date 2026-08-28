from PySide6.QtGui import QPixmap


class SymbolMapper:
    def __init__(self):
        self._character_map = {}  ## {char: pixmap}
        self._valid_extensions = {".png", ".jpg", ".jpeg"}

    def get_pixmap(self, character: str) -> QPixmap:
        return self._character_map.get(character, QPixmap())

    def set_pixmap(self, char: str, pixmap: QPixmap):
        if pixmap and not pixmap.isNull():
            self._character_map[char] = pixmap

    def has_image(self, character: str) -> bool:
        return character in self._character_map

    def clear_map(self):
        self._character_map.clear()
