from typing import Optional

from pydantic import BaseModel, Field


class SavedFileDTO(BaseModel):
    version: str = Field(default="1.0")
    content: str
    imageSize: int | None = None
    collectionName: str = ""

    class Config:
        extra = "ignore"
