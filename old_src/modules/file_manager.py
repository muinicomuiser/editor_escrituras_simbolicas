from PySide6.QtWidgets import (
    QFileDialog,
    QMessageBox,
    QWidget,
)
from PySide6.QtCore import QJsonDocument

   # ---- LÓGICA DE ARCHIVOS (PERSISTENCIA Y EXPORTACIÓN) ----

   #### El FileManager también debería conservar el nombre del archivo, en vez del main window
   #### Y también el estado de guardado o no guardado
class FileManager:
    def __init__(self):
        self._saved = False   

    def set_to_unsaved(self):
        self._saved = False    

    def set_to_saved(self):
        self._saved = True    


    def openFile(self, window: QWidget):
        
        file_name, _ = QFileDialog.getOpenFileName(
            window, "Abrir Proyecto", "", "Archivo de Proyecto (*.json)"
        )
        if not file_name:
            return

        try:
            with open(file_name, "r", encoding="utf-8") as f:
                data = f.read()
        except Exception as e:
            QMessageBox.critical(
                window, "Error", f"No se pudo abrir el archivo: {str(e)}"
            )

        json_doc = QJsonDocument.fromJson(data.encode("utf-8"))
        if json_doc.isNull() or not json_doc.isObject():
            QMessageBox.critical(window, "Error", "El archivo no es un proyecto válido.")
            return

        project_obj = json_doc.object()
        text_content = project_obj.get("content", "")
        _saved_size = project_obj.get("imageSize", 32)
        _saved_dir = project_obj.get("assetsDirectory", "assets/default_set")

        self.set_to_saved()
            
        return (text_content, _saved_size, _saved_dir, file_name)


    def saveFileAs(self, window, project_dict):
        file_name, _ = QFileDialog.getSaveFileName(
            window, "Guardar Proyecto", "untiled.json", "Archivo de Proyecto (*.json)"
        )
        if not file_name:
            return

        if not file_name.lower().endswith(".json"):
            file_name += ".json"

        try:
            # doc = QJsonDocument.fromJson(json.dumps(project_dict).encode("utf8")) # Este método ejecuta una doble serialización
            doc = QJsonDocument.fromVariant(project_dict) # Este método ejecuta una sola serialización
            with open(file_name, "w", encoding="utf-8") as f:
                f.write(
                    doc.toJson(QJsonDocument.JsonFormat.Indented).data().decode("utf-8")
                )
            self.set_to_saved()              

        except Exception as e:
            QMessageBox.critical(
                window, "Error", f"No se pudo crear el archivo de proyecto: {str(e)}"
            )

        return file_name

    def saveFile(self, window: QWidget, project_dict: dict, file_name: str):

        if self._saved:
            return

        if not file_name.lower().endswith(".json"):
            file_name += ".json"

        try:
            doc = QJsonDocument.fromVariant(project_dict)
            with open(file_name, "w", encoding="utf-8") as f:
                f.write(
                    doc.toJson(QJsonDocument.JsonFormat.Indented).data().decode("utf-8")
                )
            self.set_to_saved()                
        except Exception as e:
            QMessageBox.critical(
                window, "Error", f"No se pudo guardar el archivo de proyecto: {str(e)}"
            )
            return
