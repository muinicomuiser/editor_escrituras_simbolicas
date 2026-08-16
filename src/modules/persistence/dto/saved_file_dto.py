from pydantic import BaseModel, Field


class SavedFileDTO(BaseModel):
    version: str = Field(default="1.0")
    content: str
    imageSize: int
    collectionName: str

    class Config:
        extra = "ignore"