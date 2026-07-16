import os


class SymbolMapper:
    def __init__(self):
        self._character_map = {}
        self._current_dir = "assets/default_set"
        self.load_default_set()

    def load_default_set(self):
        self._character_map.clear()
        base_dir = "assets/default_set"

        if not os.path.exists(base_dir) or not os.path.isdir(base_dir):
            return

        valid_extensions = {".png", ".jpg", ".jpeg"}

        for entry in os.scandir(base_dir):
            if entry.is_file():
                filename, ext = os.path.splitext(entry.name)
                if ext.lower() in valid_extensions:
                    if len(filename) == 1:
                        char_key = filename[0]
                        self._character_map[char_key] = entry.path
                    elif filename.lower() == "space":
                        self._character_map[" "] = entry.path

    def get_image_path(self, character: str) -> str:
        return self._character_map.get(character, "")

    def has_image(self, character: str) -> bool:
        return character in self._character_map

    def load_from_directory(self, path: str):
        self._character_map.clear()
        self._current_dir = path

        if not os.path.exists(path) or not os.path.isdir(path):
            return

        valid_extensions = {".png", ".jpg", ".jpeg"}

        for entry in os.scandir(path):
            if entry.is_file():
                filename, ext = os.path.splitext(entry.name)
                if ext.lower() in valid_extensions:
                    if filename:
                        # Se toma el primer carácter como clave para el mapeo
                        char_key = filename[0]
                        self._character_map[char_key] = entry.path

    def get_current_directory(self) -> str:
        return self._current_dir
