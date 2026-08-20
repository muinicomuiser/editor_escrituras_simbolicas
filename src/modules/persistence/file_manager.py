import json
from modules.persistence.dto.saved_file_dto import SavedFileDTO
from modules.shared.models.project_model import ProjectModel

# ---- LÓGICA DE ARCHIVOS (PERSISTENCIA Y EXPORTACIÓN) ----


## Anotación: El DTO es un contrato entre esta clase y el sistema de archivos o persistencia,
# no participa en otras partes de la aplicación
class FileManager:
    def __init__(self):
        self._saved = False
        self._current_filename = None
        self._file_extension = ".json"

    def set_to_unsaved(self):
        self._saved = False

    def set_to_saved(self):
        self._saved = True

    def get_current_filename(self):
        return (
            self._current_filename.removesuffix(self._file_extension)
            if self._current_filename
            else None
        )

    def get_file_extension(self):
        return self._file_extension

    def openFile(self, file_name: str):
        with open(file_name, "r", encoding="utf-8") as f:
            raw_data = json.load(f)
        dto = SavedFileDTO.model_validate(raw_data)

        self._saved = True
        self._current_filename = file_name

        return self._toDomain(dto)

    def saveFile(self, entity: ProjectModel):

        if not self._current_filename:
            raise FileNotFoundError("No hay ruta asignada.")

        if not self._saved:
            dto: SavedFileDTO = self._toDTO(entity)
            with open(self._current_filename, "w", encoding="utf-8") as f:
                f.write(dto.model_dump_json(indent=2))
            self._saved = True

    def saveFileAs(self, file_name: str, entity: ProjectModel):

        if not file_name.lower().endswith(self._file_extension):
            file_name += self._file_extension
        dto: SavedFileDTO = self._toDTO(entity)
        with open(file_name, "w", encoding="utf-8") as f:
            f.write(dto.model_dump_json(indent=2))
        self._saved = True
        self._current_filename = file_name

    def _toDTO(self, entity: ProjectModel) -> SavedFileDTO:
        return SavedFileDTO(
            version=entity.version,
            collectionName=entity.collectionName,
            content=entity.content,
            imageSize=entity.imageSize,
        )

    def _toDomain(self, dto: SavedFileDTO) -> ProjectModel:
        return ProjectModel(
            version=dto.version,
            collectionName=dto.collectionName,
            content=dto.content,
            imageSize=dto.imageSize,
        )
