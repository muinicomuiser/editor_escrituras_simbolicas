from pathlib import Path
import shutil
from PySide6.QtCore import QByteArray
from modules.utils.logger import get_logger
from modules.exceptions.exceptions import StorageError, DirectoryRemovalError

# ---- LÓGICA DE ARCHIVOS (PERSISTENCIA Y EXPORTACIÓN) ----

class FilesService:
    def __init__(self):

        self.logger = get_logger(self.__class__.__name__)
        self.logger.info(f"Módulo Iniciado")           
        

    def save(self, file_name: str | Path, bytes_array: QByteArray | bytearray):
        file_path = file_name if isinstance(file_name, Path)  else  Path(file_name)
        try:
            if not file_path.parent.exists():
                file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_bytes(bytes_array.data())
        except OSError as e:
            raise StorageError(f"Fallo al guardar el archivo: {e}")

    def open(self, file_name: str | Path) -> bytes | bytearray:
        file_path = file_name if isinstance(file_name, Path)  else  Path(file_name)
        try:
            if not file_path.exists():
                return None
            else:
                return file_path.read_bytes()
        except OSError as e:
            raise StorageError(f"Fallo al abrir el archivo: {e}")        
        
    def read_dir(self, dir: str | Path) -> list[Path]:
        dir_path = dir if isinstance(dir, Path) else Path(dir)
        try:
            files = [f for f in dir_path.iterdir() if f.is_file()]
            return files
        except OSError as e:
            raise StorageError(f"Fallo al leer el directorio: {e}")        
        
    def delete(self, file_name: str | Path):
        file_path = file_name if isinstance(file_name, Path) else Path(file_name)
        try:
            if file_path.exists() and file_path.is_file():
                file_path.unlink()
        except OSError as e:
            raise StorageError(f"Fallo al remover el archivo {file_path}: {e}")
        
    def remove_dir(self, dir: str | Path):
        dir_path = dir if isinstance(dir, Path) else Path(dir)
        try:
            if dir_path.exists():
                shutil.rmtree(dir_path)
        except OSError as e:
            raise DirectoryRemovalError(f"Fallo al eliminar el directorio: {e}")           
