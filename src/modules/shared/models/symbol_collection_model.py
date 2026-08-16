from pydantic import BaseModel

class SymbolCollectionModel(BaseModel):
    collection_name: str
    directory: str

    class Config:
        extra = "ignore"

class SavedSymbolsCollectionFileModel(BaseModel):
    collections: list[SymbolCollectionModel]
