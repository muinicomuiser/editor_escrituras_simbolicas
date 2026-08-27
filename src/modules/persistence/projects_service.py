import json
from pathlib import Path
from modules.persistence.dto.saved_file_dto import SavedFileDTO
from modules.shared.models.project_model import ProjectModel
from modules.utils.logger import get_logger
from modules.exceptions.exceptions import StorageError, UndefinedPathError
# logger = get_logger(__name__)

# ---- LÓGICA DE ARCHIVOS (PERSISTENCIA Y EXPORTACIÓN) ----


## Anotación: El DTO es un contrato entre esta clase y el sistema de archivos o persistencia,
# no participa en otras partes de la aplicación
class ProjectsService:
    def __init__(self):

        self._saved = True
        self._current_filepath: str = None
        self._file_extension = ".json"
        self.logger = get_logger(self.__class__.__name__)
        self.logger.info(f"Módulo Iniciado")           

    def set_to_unsaved(self):
        """Marca el estado de guardado del archivo actual como no guardado (false)"""
        self._saved = False

    def set_to_saved(self):
        """Marca el estado de guardado del archivo actual como guardado (true)"""
        self._saved = True

    def is_saved(self):
        """Retorna el estado de guardado del archivo actual (true=guardado, false=no guardado)"""
        return self._saved

    def get_current_filepath(self):
        """Retorna la ruta completa del archivo actual, incluyendo la extensión"""
        return self._current_filepath

    def get_current_filename(self):
        """Retorna el nombre del archivo actual, sin extensión"""
        return (
            self._current_filepath.removesuffix(self._file_extension)
            if self._current_filepath
            else None
        )

    def get_file_extension(self):
        """Retorna la extensión del tipo de archivo de guardado de los proyectos"""
        return self._file_extension

    def open(self, file_name: str) -> ProjectModel:
        """Abre el archivo en la ruta específica y lo retorna como entidad. 
        Registra el estado del archivo como guardado y almacena el nombre del archivo para trabajarlo
        como el archivo actual del proyecto en el editor.        
        """
        try:
            file_path = Path(file_name)
            if not file_path.exists():
                raise FileNotFoundError(f"El archivo no existe: {file_path}")
            with file_path.open("r", encoding="utf-8") as f:
                raw_data = json.load(f)
            dto = SavedFileDTO.model_validate(raw_data)
            self._saved = True
            self._current_filepath = file_name
        except (OSError, PermissionError) as e:
            raise StorageError(f"Fallo al acceder al archivo: {e}")

        return self._toDomain(dto)

    def save(self, entity: ProjectModel, file_name: str = None):

        if not file_name and not self._current_filepath:
            raise UndefinedPathError("No hay ruta asignada para guardar el archivo.")

        try:
            dto: SavedFileDTO = self._toDTO(entity)
            file_path_str = file_name if file_name else self._current_filepath
            file_path = Path(file_path_str)
            if not file_path.parent.exists():
                file_path.parent.mkdir(parents=True, exist_ok=True)
            with file_path.open("w", encoding="utf-8") as f:
                f.write(dto.model_dump_json(indent=2))
            self._saved = True
            self._current_filepath = file_path_str
        except (OSError, PermissionError) as e:
            raise StorageError(f"Fallo al guardar el archivo: {e}")

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
