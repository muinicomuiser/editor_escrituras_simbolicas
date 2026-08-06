import os
import sys

class SymbolMapper:
    def __init__(self):
        self._character_map = {}
        self._default_symbols_dir = os.path.join(getattr(sys, '_MEIPASS', os.path.abspath(".")), "simbolos")
        self._current_dir = os.path.join(self._default_symbols_dir, "ejemplo")
        self._valid_extensions = {".png", ".jpg", ".jpeg"}
        self.load_from_directory(self._current_dir)

    def get_current_directory(self) -> str:
        return self._current_dir

    def get_image_path(self, character: str) -> str:
        return self._character_map.get(character, "")   

    def has_image(self, character: str) -> bool:
        return character in self._character_map     

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
                        self._character_map[char_key] = entry.path
                    elif filename.lower() == "space": 
                        self._character_map[" "] = entry.path
