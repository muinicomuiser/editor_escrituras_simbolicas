import json
import os
import sys
from pathlib import Path
from modules.persistence.dto.saved_symbols_coll_file_dto import SavedSymbolsCollectionFileDTO, SymbolCollectionDTO
from modules.shared.models.symbol_collection_model import SavedSymbolsCollectionFileModel, SymbolCollectionModel

# ---- LÓGICA DE ARCHIVOS (PERSISTENCIA Y EXPORTACIÓN) ----

## Anotación: El DTO es un contrato entre esta clase y el sistema de archivos o persistencia, 
# no participa en otras partes de la aplicación
class SymbolsCollectionFileManager:
    def __init__(self):
        self._saved = False
        self._current_filename = None
        self._file_extension = "json"
        self._collections_persistence_dir = os.path.join(getattr(sys, '_MEIPASS', os.path.abspath(".")), "simbolos")
        self.collections_persistence_file = os.path.join(self._collections_persistence_dir, "symbol_collections.json")      
        self._setup_collection_file() 

    def set_to_unsaved(self):
        self._saved = False

    def set_to_saved(self):
        self._saved = True

    def get_current_filename(self):
        return self._current_filename

    def get_file_extension(self):
        return self._file_extension

    def openFile(self, file_name: str):
        with open(file_name, "r", encoding="utf-8") as f:
            raw_data = json.load(f)
        dto = SavedSymbolsCollectionFileDTO.model_validate(raw_data)

        self._saved = True
        self._current_filename = file_name

        return self._toDomain(dto)

    def saveFile(self, entity: SavedSymbolsCollectionFileModel):

        if not self._current_filename:
            raise FileNotFoundError("No hay ruta asignada.")

        if not self._saved:
            dto: SavedSymbolsCollectionFileDTO = self._toDTO(entity)            
            with open(self._current_filename, "w", encoding="utf-8") as f:
                f.write(dto.model_dump_json(indent=2))
            self._saved = True

    def saveFileAs(self, file_name: str, entity: SavedSymbolsCollectionFileModel):

        file_extension = f".{self._file_extension}"
        if not file_name.lower().endswith(file_extension):
            file_name += file_extension
        dto: SavedSymbolsCollectionFileDTO = self._toDTO(entity)
        with open(file_name, "w", encoding="utf-8") as f:
            f.write(dto.model_dump_json(indent=2))
        self._saved = True
        self._current_filename = file_name


    def _setup_collection_file(self): # Acá falta manejo de excepciones
        dir_path = Path(self._collections_persistence_dir)
        file_path = Path(self.collections_persistence_file)
        if not dir_path.is_dir():
            Path(self._collections_persistence_dir).mkdir(exist_ok=True)
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
    