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

    # def load_from_directory(self, path: str):
    #     self._character_map.clear()
    #     self._current_dir = path

    #     if not os.path.exists(path) or not os.path.isdir(path):
    #         return

    #     for entry in os.scandir(path):
    #         if entry.is_file():
    #             filename, ext = os.path.splitext(entry.name)
    #             if ext.lower() in self._valid_extensions:
    #                 if filename:
    #                     char_key = filename[0]
    #                     # self._character_map[char_key] = entry.path
    #                     self._character_map[char_key] = QPixmap(entry.path)
    #                 elif filename.lower() == "space":
    #                     # self._character_map[" "] = entry.path
    #                     self._character_map[" "] = QPixmap(entry.path)
    #                 # if filename:
    #                 #     char_key = filename[0]
    #                 #     print(char_key)
    #                 #     self._character_map[char_key]["image_path"] = entry.path
    #                 # elif filename.lower() == "space":
    #                 #     self._character_map[" "]["image_path"]  = entry.path
