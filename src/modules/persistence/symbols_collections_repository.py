import json
import os
import sys
import shutil
from pathlib import Path
from modules.persistence.dto.saved_symbols_coll_file_dto import (
    SavedSymbolsCollectionFileDTO,
    SymbolCollectionDTO,
)
from modules.shared.models.symbol_collection_model import (
    SavedSymbolsCollectionFileModel,
    SymbolCollectionModel,
)

# ---- LÓGICA DE ARCHIVOS (PERSISTENCIA Y EXPORTACIÓN) ----
### Igual tengo que ver si la lógica de guardado de imágenes de colecciones irá acá

## Anotación: El DTO es un contrato entre esta clase y el sistema de archivos o persistencia,
# no participa en otras partes de la aplicación

class SymbolsCollectionRepository:
    def __init__(self):
        self._saved = True
        self._file_extension = ".json"
        self._collections_persistence_dir = Path(
            getattr(sys, "_MEIPASS", os.path.abspath(".")), "data/simbolos"
        )
        self.collections_persistence_file = self._collections_persistence_dir.joinpath(
            "symbol_collections.json"
        )
        self._setup_collection_file()
        self._data = self._load_to_memory()

    def set_to_unsaved(self):
        self._saved = False

    def set_to_saved(self):
        self._saved = True

    def is_saved(self):
        return self._saved

    def get_collections_persistence_dir(self):
        return self._collections_persistence_dir

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

    ## Agregar manejo de excepciones, si es que no logra reemplazar o guardar
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
            old_path = self._collections_persistence_dir.joinpath(existing.directory)
            new_dir = update.directory
            new_path = self._collections_persistence_dir.joinpath(new_dir)

            self._data.collections[index].collection_name = (
                update.collection_name
            )
            self._data.collections[index].directory = new_dir

            old_path.rename(new_path)
            self._commit()

        else:
            self.save(update)

    def delete(self, collection_name: str):
        index, existing = next(
            (
                (index, collection)
                for index, collection in enumerate(self._data.collections)
                if collection.collection_name == collection_name
            ),
            None,
        )
        if existing:
            old_path = self._collections_persistence_dir.joinpath(existing.directory)
            try:
                if old_path.exists():
                    shutil.rmtree(old_path)
            except OSError as e:
                print(f"Error al borrar el directorio: {e}")
                return                
            self._data.collections.pop(index)
            self._commit()

    def _setup_collection_file(self):  # Acá falta manejo de excepciones
        try:
            if not self._collections_persistence_dir.is_dir():
                Path(self._collections_persistence_dir).mkdir(exist_ok=True, parents=True)
            if not self.collections_persistence_file.exists():
                payload = {"collections": []}
                with self.collections_persistence_file.open("w", encoding="utf-8") as file:
                    json.dump(payload, file, indent=4)

        except OSError as e:
            print(f"Error al crear la estructura de directorios: {e}")

    def _load_to_memory(self) -> SavedSymbolsCollectionFileModel:
            try:
                with self.collections_persistence_file.open("r", encoding="utf-8") as f:
                    raw_data = json.load(f)
                file_dto = SavedSymbolsCollectionFileDTO.model_validate(raw_data)
                return self._toDomain(file_dto)
            except (json.JSONDecodeError, FileNotFoundError) as e:
                print(f"Error leyendo el JSON: {e}. Retornando lista vacía.")
                return SavedSymbolsCollectionFileModel(collections=[])

    def _commit(self):

        dto: SavedSymbolsCollectionFileDTO = self._toDTO(self._data)
        with self.collections_persistence_file.open("w", encoding="utf-8") as f:
            f.write(dto.model_dump_json(indent=2))
        self._saved = True

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


