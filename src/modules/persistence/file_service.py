from pathlib import Path
from PySide6.QtCore import QByteArray
from modules.utils.logger import get_logger
from modules.exceptions.exceptions import StorageError

# ---- LÓGICA DE ARCHIVOS (PERSISTENCIA Y EXPORTACIÓN) ----

class FilesService:
    def __init__(self):

        self.logger = get_logger(self.__class__.__name__)
        self.logger.info(f"Módulo Iniciado")           


    def save(self, file_name: str | Path, bytes_array: QByteArray | bytearray):
        try:
            file_path = file_name if isinstance(file_name, Path)  else  Path(file_name)
            if not file_path.parent.exists():
                file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_bytes(bytes_array.data())
        except OSError as e:
            raise StorageError(f"Fallo al guardar el archivo: {e}")
