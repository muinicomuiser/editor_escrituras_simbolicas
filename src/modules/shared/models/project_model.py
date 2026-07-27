from pydantic import BaseModel


class ProjectModel(BaseModel):

    version: str
    content: str
    imageSize: int
    assetsDirectory: str