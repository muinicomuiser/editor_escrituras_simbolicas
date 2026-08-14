import os
import sys

from PySide6.QtGui import QPixmap

class SymbolMapper:
    def __init__(self):
        self._character_map = {} ## {char: pixmap}
        self._default_symbols_dir = os.path.join(getattr(sys, '_MEIPASS', os.path.abspath(".")), "simbolos")
        self._current_dir = os.path.join(self._default_symbols_dir, "ejemplo")
        self._valid_extensions = {".png", ".jpg", ".jpeg"}
        # self.load_from_directory(self._current_dir)

    def get_pixmap(self, character: str) -> QPixmap:
        return self._character_map.get(character, QPixmap())

    def set_pixmap(self, char: str, pixmap: QPixmap):
        self._character_map[char] = pixmap 

    def get_current_directory(self) -> str:
        return self._current_dir

    def has_image(self, character: str) -> bool:
        return character in self._character_map     
    def clear_map(self):
        self._character_map.clear()
    

    # def get_image_path(self, character: str) -> str:
    #     return self._character_map.get(character, "")   
    # def get_image_path(self, character: str) -> str:

    #     char_map = self._character_map[character]
    #     return char_map.get("image_path", "") if char_map else ""


    def load_from_directory(self, path: str):
        self._character_map.clear()
        self._current_dir = path

        if not os.path.exists(path) or not os.path.isdir(path):
            return

        for entry in os.scandir(path):
            if entry.is_file():
                filename, ext = os.path.splitext(entry.name)
                if ext.lower() in self._valid_extensions:
                    if filename:
                        char_key = filename[0]
                        # self._character_map[char_key] = entry.path
                        self._character_map[char_key] = QPixmap(entry.path)
                    elif filename.lower() == "space": 
                        # self._character_map[" "] = entry.path
                        self._character_map[" "] = QPixmap(entry.path)
                    # if filename:
                    #     char_key = filename[0]
                    #     print(char_key)
                    #     self._character_map[char_key]["image_path"] = entry.path
                    # elif filename.lower() == "space": 
                    #     self._character_map[" "]["image_path"]  = entry.path
