from datetime import datetime
import json
import os
import sys
from pathlib import Path

from pydantic import ValidationError
from modules.persistence.dto.saved_symbols_coll_file_dto import (
    SavedSymbolsCollectionFileDTO,
    SymbolCollectionDTO,
)
from modules.shared.models.symbol_collection_model import (
    SavedSymbolsCollectionFileModel,
    SymbolCollectionModel,
)
from modules.utils.logger import get_logger
from modules.exceptions.exceptions import StorageError

# ---- LÓGICA DE ARCHIVOS (PERSISTENCIA Y EXPORTACIÓN) ----
### Igual tengo que ver si la lógica de guardado de imágenes de colecciones irá acá

class SymbolsCollectionRepository:
    def __init__(self):
        self._saved = True
        self._file_extension = ".json"
        self._collections_dir = Path(
            getattr(sys, "_MEIPASS", os.path.abspath(".")), "data/simbolos"
        )
        self.collections_catalog_file = self._collections_dir.joinpath(
            "symbol_collections.json"
        )

        self._collections_backup_dir = self._collections_dir.joinpath("backup")
        
        # Logger
        self.logger = get_logger(self.__class__.__name__)
        self.logger.info(f"Módulo Iniciado")      

        self._setup_collection_file()
        self._data = self._load_to_memory()

    def set_to_unsaved(self):
        self._saved = False

    def set_to_saved(self):
        self._saved = True

    def is_saved(self):
        return self._saved

    def get_collections_dir(self):
        return self._collections_dir

    def findAll(self):
        collections_data = self._data.collections
        return collections_data
    
    def save(self, collection: SymbolCollectionModel):

        self._data.collections.append(collection)
        self._commit()

    def findByName(self, name: str) -> SymbolCollectionModel | None:
        collection = next(
            (
                item
                for item in self._data.collections
                if item.collection_name == name
            ),
            None,
        )
        return collection

    ## no está devolviendo nada
    def update(
        self, collection_name: str, update: SymbolCollectionModel
    ) -> SymbolCollectionModel:
        
        match = next(
            (
                (index, collection)
                for index, collection in enumerate(self._data.collections)
                if collection.collection_name == collection_name
            ),
            None,
        )
        if match:
            index, existing = match
            old_path = self._collections_dir.joinpath(existing.directory)
            new_dir = update.directory
            new_path = self._collections_dir.joinpath(new_dir)

            self._data.collections[index].collection_name = (
                update.collection_name
            )
            self._data.collections[index].directory = new_dir

            old_path.rename(new_path)
            self._commit()

        else:
            self.save(update)

    def delete(self, collection_name: str):
        match = next(
            (
                (index, collection)
                for index, collection in enumerate(self._data.collections)
                if collection.collection_name == collection_name
            ),
            None,
        )
        if match:
            index, collection = match
            self._data.collections.pop(index)
            self._commit()

    def _setup_collection_file(self):
        try:
            if not self._collections_dir.is_dir():
                self._collections_dir.mkdir(exist_ok=True, parents=True)
            if not self.collections_catalog_file.exists():
                payload = {"collections": []}
                with self.collections_catalog_file.open("w", encoding="utf-8") as file:
                    json.dump(payload, file, indent=4)
        except OSError as e:
            raise StorageError(f"Fallo al crear el archivo de colecciones: {e}")

    def _load_to_memory(self) -> SavedSymbolsCollectionFileModel:
            if not self.collections_catalog_file.exists():
                self._setup_collection_file()
            try:
                with self.collections_catalog_file.open("r", encoding="utf-8") as f:
                    raw_data = json.load(f)
                file_dto = SavedSymbolsCollectionFileDTO.model_validate(raw_data)
                return self._toDomain(file_dto)
            except (json.JSONDecodeError, ValidationError) as e:
                self.logger.error(f"Archivo de datos de colecciones corrupto, respaldando y recreando: {e}")
                try:
                    self._collections_backup_dir.mkdir(exist_ok=True, parents=True)
                    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
                    backup_name = f"backup_{timestamp_str}.json"
                    new_backup_filepath = self._collections_backup_dir.joinpath(backup_name)
                    self.collections_catalog_file.rename(new_backup_filepath)
                    self._setup_collection_file()
                    return SavedSymbolsCollectionFileModel(collections=[])
                except OSError as backup_error:
                    raise StorageError(f"Fallo al respaldar el archivo corrupto de colecciones: {backup_error}")
            except OSError as e:
                raise StorageError(f"Fallo al acceder al archivo de colecciones: {e}")

    def _commit(self):

        dto: SavedSymbolsCollectionFileDTO = self._toDTO(self._data)
        try:
            with self.collections_catalog_file.open("w", encoding="utf-8") as f:
                f.write(dto.model_dump_json(indent=2))
            self._saved = True
        except OSError as e:
            raise StorageError(f"Fallo al guardar archivo: {e}")

    def _toDTO(
        self, entity: SavedSymbolsCollectionFileModel
    ) -> SavedSymbolsCollectionFileDTO:
        dto_collections_list = [
            SymbolCollectionDTO.fromEntity(item) for item in entity.collections
        ]
        return SavedSymbolsCollectionFileDTO(collections=dto_collections_list)

    def _toDomain(
        self, dto: SavedSymbolsCollectionFileDTO
    ) -> SavedSymbolsCollectionFileModel:
        model_collections_list = [item.toEntity() for item in dto.collections]
        return SavedSymbolsCollectionFileModel(collections=model_collections_list)


