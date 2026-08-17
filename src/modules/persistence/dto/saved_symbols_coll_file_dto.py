from pydantic import BaseModel
from modules.shared.models.symbol_collection_model import (
    SavedSymbolsCollectionFileModel,
    SymbolCollectionModel,
)


class SymbolCollectionDTO(BaseModel):
    collection_name: str
    directory: str

    class Config:
        extra = "ignore"

    @staticmethod
    def fromEntity(entity):
        return SymbolCollectionDTO(
            collection_name=entity.collection_name, directory=entity.directory
        )

    def toEntity(self):
        return SymbolCollectionModel(
            collection_name=self.collection_name, directory=self.directory
        )


class SavedSymbolsCollectionFileDTO(BaseModel):
    collections: list[SymbolCollectionDTO]

    @staticmethod
    def fromEntity(entity):
        return SavedSymbolsCollectionFileDTO(collections=entity.collections)

    def toEntity(self):
        return SavedSymbolsCollectionFileModel(collections=self.collections)
