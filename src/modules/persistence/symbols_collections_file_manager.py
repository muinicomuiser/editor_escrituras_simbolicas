import json
import os
import sys
from pathlib import Path
from modules.persistence.dto.saved_symbols_coll_file_dto import SavedSymbolsCollectionFileDTO, SymbolCollectionDTO
from modules.shared.models.symbol_collection_model import SavedSymbolsCollectionFileModel, SymbolCollectionModel

# ---- LÓGICA DE ARCHIVOS (PERSISTENCIA Y EXPORTACIÓN) ----
### Aunque esto es más bien un repository
### Igual tengo que ver si la lógica de guardado de imágenes de colecciones irá acá

## Anotación: El DTO es un contrato entre esta clase y el sistema de archivos o persistencia, 
# no participa en otras partes de la aplicación
class SymbolsCollectionFileManager:
    def __init__(self):
        self._saved = False
        self._current_filename = None
        self._file_extension = "json"
        # self._collections_persistence_dir = os.path.join(getattr(sys, '_MEIPASS', os.path.abspath(".")), "data/simbolos")
        self._collections_persistence_dir = Path(getattr(sys, '_MEIPASS', os.path.abspath(".")), "data/simbolos")
        # self.collections_persistence_file = os.path.join(self._collections_persistence_dir, "symbol_collections.json")      
        self.collections_persistence_file = self._collections_persistence_dir.joinpath("symbol_collections.json")
        self._setup_collection_file() 

    def set_to_unsaved(self):
        self._saved = False

    def set_to_saved(self):
        self._saved = True

    def is_saved(self):
        return self._saved

    def get_collections_persistence_dir(self):
        return self._collections_persistence_dir

    # def get_file_extension(self):
    #     return self._file_extension

    def openFile(self):
        with self.collections_persistence_file.open("r", encoding="utf-8") as f:
            raw_data = json.load(f)
        dto = SavedSymbolsCollectionFileDTO.model_validate(raw_data)

        self._saved = True

        return self._toDomain(dto)
    
    # def openFile(self, file_name: str):
    #     with open(file_name, "r", encoding="utf-8") as f:
    #         raw_data = json.load(f)
    #     dto = SavedSymbolsCollectionFileDTO.model_validate(raw_data)

    #     self._saved = True
    #     self._current_filename = file_name

    #     return self._toDomain(dto)

    def saveFile(self, entity: SavedSymbolsCollectionFileModel):
        if not self.collections_persistence_file:
            raise FileNotFoundError("No hay ruta asignada.")

        self.saveFileAs(entity)
        self._saved = True
    #     if not self._saved:
    #         dto: SavedSymbolsCollectionFileDTO = self._toDTO(entity)            
    #         with open(self._current_filename, "w", encoding="utf-8") as f:
    #             f.write(dto.model_dump_json(indent=2))
    #         self._saved = True
            
    # def saveFile(self, entity: SavedSymbolsCollectionFileModel):
    #     if not self._current_filename:
    #         raise FileNotFoundError("No hay ruta asignada.")

    #     if not self._saved:
    #         dto: SavedSymbolsCollectionFileDTO = self._toDTO(entity)            
    #         with open(self._current_filename, "w", encoding="utf-8") as f:
    #             f.write(dto.model_dump_json(indent=2))
    #         self._saved = True

    def saveFileAs(self, entity: SavedSymbolsCollectionFileModel):

        dto: SavedSymbolsCollectionFileDTO = self._toDTO(entity)
        with self.collections_persistence_file.open("w", encoding="utf-8") as f:
            f.write(dto.model_dump_json(indent=2))
        self._saved = True

    def add_collection(self, collection: SymbolCollectionModel):
        ## Ver también si puedo dejar abierta la conexión con el archivo, o cómo abordar eso
        collections_data = self.openFile()
        collections_data.collections.append(collection)
        self.saveFileAs(collections_data)

    def find_by_name(self, name: str) -> SymbolCollectionModel | None:
        collections_data = self.openFile()
        collection = next((item for item in collections_data.collections if item.collection_name == name), None)
        return collection


    ## Agregar manejo de excepciones, si es que no logra reemplazar o guardar
    def update(self, collection_name: str, replace_collection: SymbolCollectionModel) -> SymbolCollectionModel:
        collections_data = self.openFile()
        index, existing = next(((index, collection) for index, collection in enumerate(collections_data.collections) if collection.collection_name == collection_name), None)
        if existing:
            old_path = self._collections_persistence_dir.joinpath(existing.directory)
            new_dir = replace_collection.directory
            new_path = self._collections_persistence_dir.joinpath(new_dir)

            # new_collection = SymbolCollectionModel(collection_name=collection_name, directory=new_dir)

            # collections_data.collections.pop(index)
            # collections_data.collections.append(new_collection)
            collections_data.collections[index].collection_name = replace_collection.collection_name
            collections_data.collections[index].directory = new_dir

            # existing.collection_name = replace_collection.collection_name
            # existing.directory = new_dir
            old_path.rename(new_path)
            self.saveFile(collections_data)

        else:
            self.add_collection(replace_collection)

    def delete(self, collection_name: str):
        collections_data = self.openFile()
        index, existing = next(((index, collection) for index, collection in enumerate(collections_data.collections) if collection.collection_name == collection_name), None)
        if existing:
            old_path = self._collections_persistence_dir.joinpath(existing.directory)
            files = [files for files in old_path.iterdir()]
            for file in files:
                file.unlink()
            old_path.rmdir()
            collections_data.collections.pop(index)
            self.saveFile(collections_data)            

    # def saveFileAs(self, file_name: str, entity: SavedSymbolsCollectionFileModel):

    #     file_extension = f".{self._file_extension}"
    #     if not file_name.lower().endswith(file_extension):
    #         file_name += file_extension
    #     dto: SavedSymbolsCollectionFileDTO = self._toDTO(entity)
    #     with open(file_name, "w", encoding="utf-8") as f:
    #         f.write(dto.model_dump_json(indent=2))
    #     self._saved = True
    #     self._current_filename = file_name


    def _setup_collection_file(self): # Acá falta manejo de excepciones
        dir_path = Path(self._collections_persistence_dir)
        file_path = Path(self.collections_persistence_file)
        if not dir_path.is_dir():
            Path(self._collections_persistence_dir).mkdir(exist_ok=True, parents=True)
        if not file_path.exists():
            payload = {
                "collections": []
            }
            with file_path.open("w", encoding="utf-8") as file:
                json.dump(payload, file, indent=4)


    ## Habrá que revisar acá cómo hacer la conversión de colecciones, o cuando no tenga tanto sueño hacerlo bien
    def _toDTO(self, entity: SavedSymbolsCollectionFileModel) -> SavedSymbolsCollectionFileDTO:
        dto_collections_list = [SymbolCollectionDTO.fromEntity(item) for item in entity.collections]
        return SavedSymbolsCollectionFileDTO(
            collections = dto_collections_list
        )

    def _toDomain(self, dto: SavedSymbolsCollectionFileDTO) -> SavedSymbolsCollectionFileModel:
        model_collections_list = [item.toEntity() for item in dto.collections]
        return SavedSymbolsCollectionFileModel(
            collections = model_collections_list
        )
    