from PySide6.QtWidgets import (
    QFileDialog,
    QMessageBox,
    QWidget,
)
from PySide6.QtCore import QJsonDocument
from modules.persistence.dto.saved_file_dto import SavedFileDTO
# ---- LÓGICA DE ARCHIVOS (PERSISTENCIA Y EXPORTACIÓN) ----


## TODO: DTOs, conversión DTO-Domain y validaciones

## Anotación: El DTO es un contrato entre esta clase y el sistema de archivos o persistencia, 
# no participa en otras partes de la aplicación
class FileManager:
    def __init__(self):
        print("On Redo FileManager")
        self._saved = False
        self._current_filename = None
        self._file_extension = "json"

    def set_to_unsaved(self):
        self._saved = False

    def set_to_saved(self):
        self._saved = True

    def get_current_filename(self):
        return self._current_filename

    def get_file_extension(self):
        return self._file_extension

    def openFile(self, file_name: str): # Debería devolver el domain
        with open(file_name, "r", encoding="utf-8") as f:
            data = f.read()
        json_doc = QJsonDocument.fromJson(data.encode("utf-8"))

        if json_doc.isNull() or not json_doc.isObject():
            raise ValueError("El archivo no es un proyecto válido.")

        project_obj = json_doc.object()
        dto = SavedFileDTO.model_validate(project_obj)

        self._saved = True
        self._current_filename = file_name

        return project_obj

    def saveFileAs(self, file_name: str, project_dict): # Debería recibir el domain

        file_extension = f".{self._file_extension}"
        if not file_name.lower().endswith(file_extension):
            file_name += file_extension

        # doc = QJsonDocument.fromJson(json.dumps(project_dict).encode("utf8")) # Este método ejecuta una doble serialización
        doc = QJsonDocument.fromVariant(
            project_dict
        )  # Este método ejecuta una sola serialización
        with open(file_name, "w", encoding="utf-8") as f:
            f.write(
                doc.toJson(QJsonDocument.JsonFormat.Indented).data().decode("utf-8")
            )
        self._saved = True
        self._current_filename = file_name

    def saveFile(self, project_dict: dict):

        if not self._saved:
            doc = QJsonDocument.fromVariant(project_dict)
            with open(self._current_filename, "w", encoding="utf-8") as f:
                f.write(
                    doc.toJson(QJsonDocument.JsonFormat.Indented).data().decode("utf-8")
                )
            self._saved = True
