from datetime import datetime
from pathlib import Path
import re
import unicodedata
from modules.shared.models.symbol_collection_model import SymbolCollectionModel
from modules.persistence.file_service import FilesService
from modules.persistence.symbols_collections_repository import SymbolsCollectionRepository
from modules.utils.logger import get_logger
from modules.exceptions.exceptions import DirectoryNotFoundError

class CollectionsService:
    def __init__(self, collections_repository: SymbolsCollectionRepository, file_service: FilesService):
        self._collections_repository = collections_repository
        self._file_service = file_service
        self._valid_extensions = {".png", ".jpg", ".jpeg"}
        self.logger = get_logger(self.__class__.__name__)
        self.logger.info(f"Módulo Iniciado")        

    def get_collections_dir(self):
        return self._collections_repository.get_collections_dir()

    def get_collections_list(self):
        return self._collections_repository.findAll()        

    def find_collection_by_name(self, name: str):
        return self._collections_repository.findByName(name)    

    def get_collection_imagepaths(self, collection: SymbolCollectionModel):    
        dir_path = self._collections_repository.get_collections_dir().joinpath(
            collection.directory
        )        
        if not dir_path.is_dir():
            raise DirectoryNotFoundError(f"Directorio no encontrado: {dir_path}")
        files = self._file_service.read_dir(dir_path)
        images_paths = [f for f in files if f.suffix.lower() in self._valid_extensions]  
        paths_dict = {}
        for image in images_paths:
            char = image.name.replace(image.suffix, "").lower()
            paths_dict[char] = image              
        return paths_dict

    def get_symbol(self, symbol_path: str | Path):
        return self._file_service.open(symbol_path)

    def get_collection_symbols(self, collection: SymbolCollectionModel):
        dir_path = self._collections_repository.get_collections_dir().joinpath(
            collection.directory
        )        
        if not dir_path.is_dir():
            raise DirectoryNotFoundError(f"Directorio no encontrado: {dir_path}")
        files = self._file_service.read_dir(dir_path)
        images_paths = [f for f in files if f.suffix.lower() in self._valid_extensions]
        symbols = {}
        for image in images_paths:
            char = image.name.replace(image.suffix, "").lower()
            symbols[char] = self._file_service.open(image)
        return symbols        

    def save_collection(self, collection: SymbolCollectionModel, symbols_data: dict ):
        collection_dir_path = self._collections_repository.get_collections_dir().joinpath(collection.directory)
        if not collection_dir_path.is_dir():
            collection_dir_path.mkdir(parents=True, exist_ok=True)
        files = {
            item.name.split(".")[0]: item for item in collection_dir_path.iterdir()
        }
        for char, image_bytes in symbols_data.items():
            if image_bytes:
                filename = collection_dir_path.joinpath(f"{char}.png")
                self._file_service.save(filename, image_bytes)
            else:
                filename = files.get(char, None)
                if filename:
                    self._file_service.delete(filename)
        exist = self._collections_repository.findByName(collection.collection_name)
        if not exist:
            self._collections_repository.save(collection)
        else:
            self._collections_repository.update(collection.collection_name, collection)
        self._collections_repository.set_to_saved()

    def update_collection(
        self, collection_name: str, update: SymbolCollectionModel
    ) -> SymbolCollectionModel:
        result = self._collections_repository.update(collection_name, update)
        self._collections_repository.set_to_saved()
        return result

    def delete_collection(self, collection: SymbolCollectionModel):
        old_path = self._collections_repository.get_collections_dir().joinpath(collection.directory)
        self._file_service.remove_dir(old_path)
        self._collections_repository.delete(collection.collection_name)
        self._collections_repository.set_to_saved()
        return old_path


    def generate_dir_name(self, collection_name: str) -> str:
        """Genera un nombre de directorio a partir de un string. Remueve y reemplaza caracteres no permitidos para nombres de directorios."""
        nfkd = unicodedata.normalize("NFKD", collection_name)
        sin_tildes = "".join([c for c in nfkd if not unicodedata.combining(c)])
        clean_name = re.sub(r"[^a-zA-Z0-9_.-]", "_", sin_tildes)
        clean_name = re.sub(r"_+", "_", clean_name).strip("_")
        timed_name = f"{clean_name}{int(datetime.now().timestamp()*1000)}"
        return timed_name.lower()
