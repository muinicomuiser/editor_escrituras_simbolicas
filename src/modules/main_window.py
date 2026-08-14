import os
import math
import textwrap
from PySide6.QtWidgets import (
    QComboBox,
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QToolBar,
    QLabel,
    QFileDialog,
    QMessageBox,
)
from PySide6.QtGui import (
    QAction,
    QKeySequence,
    QPageSize,
    QPdfWriter,
    QPainter,
    QPixmap,
)
from PySide6.QtCore import Qt, QMarginsF, QRectF
from pydantic import ValidationError

from modules.config.config import Config
from modules.editor_widget import EditorWidget
from modules.persistence.file_manager import FileManager
from modules.shared.models.project_model import ProjectModel
from modules.symbols.symbol_selector_widget import SymbolSelectorWindow
from modules.symbols.symbol_mapper import SymbolMapper

class MainWindow(QMainWindow):
    def __init__(self, config: Config, parent=None):
        super().__init__(parent)
        self.config = config

        
        self.setWindowTitle(self.config.MAIN_WINDOW_TITLE)
        self.resize(self.config.WIDTH, self.config.HEIGHT)

        # Contenedor central
        self.container = QWidget(self)
        self.setCentralWidget(self.container)
        self.container.setObjectName("MainWidget")
        self.main_layout = QHBoxLayout(self.container)

        # Symbol Mapper para inyectar en editor y ventana de colecciones
        self._symbol_mapper = SymbolMapper()        

        # Editor
        self._editor = EditorWidget(self.config, self._symbol_mapper, self)
        self.main_layout.addWidget(self._editor)
        self.main_layout.setAlignment(self._editor, Qt.AlignmentFlag.AlignHCenter)
        self.main_layout.setContentsMargins(0, 20, 0, 20)
        self._editor.setObjectName("Editor")


        # Dependencia de persistencia
        self.file_manager = FileManager()
        self._editor.textChanged.connect(
            self.file_manager.set_to_unsaved
        )

        # Prueba de ventana de drag y drop
        self._symbol_collection_editor = None

        # comandos de usuario (QActions)
        self._create_actions()

        # barra de herramientas
        self._create_toolbar()

        # menú superior
        self._create_menu_bar()


        # self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        # self.setAttribute(Qt.WA_TranslucentBackground)
        # self.setStyleSheet("""
        #     QMainWindow {
        #     }
        #     #Editor {
        #     }
        #     QLabel {
        #         color: #ffffff;
        #         font-size: 16px;
        #         font-family: 'Segoe UI', Arial, sans-serif;
        #         font-weight: bold;
        #     }
        #     QToolBar {
        #         color: #ffffff;
        #         font-size: 16px;
        #         font-family: 'Segoe UI', Arial, sans-serif;
        #         font-weight: bold;
        #     }
        #     """)

    def onToggleViewChanged(self, checked: bool): # CHECK

        if checked:
            self._toggleViewAction.setText("Modo Texto")
            self._editor.switchToTextView()
        else:
            self._toggleViewAction.setText("Modo Símbolos")
            self._editor.switchToImageView()

    ## TODO: Agregar una función que rerenderice las imágenes, sin tener que pasar a texto y a imagen nuevamente
    def onFontSizeChanged(self):

        new_size_str = self._fontSizeBox.currentText()
        if not new_size_str:
            self._fontSizeBox.setCurrentText(str(self._editor.font().pointSize()))
        elif new_size_str == str(self._editor.font().pointSize()):
            pass
        else:
            new_size = int(
                new_size_str
            )  # Falta manejar excepciones o casos en que sea un str que no pueda convertirse a int
            self._editor.setFontSize(new_size)
            if not self._toggleViewAction.isChecked():
                self._editor.switchToTextView()  # Está usando este método para pintar la nueva escala???
                self._editor.switchToImageView()
        self._editor.setFocus()

    def onSymbolsChanged(self):
        if not self._toggleViewAction.isChecked():
            self._editor.switchToTextView()  # Está usando este método para pintar la nueva escala???
            self._editor.switchToImageView()        


    ## Repasar.
    ## Acá también debería iniciarse el editor de colección de símbolos
    ## Aunque no se abra la ventana ni se actualicen las imágenes
    ## sí debería crearse la instancia del editor de colecciones, con las superficies y sus pixmaps
    ## Que el botón de abrir cree el editor de símbolos
    ## Que el botón de elegir simbolos tenga tres caminos:
    ## Crear si no se ha abierto ningún archivo (en blanco)
    ## Hacer update y show si se ha abierto un archivo con una colección elegida 

    def onOpenFile(self):  ## CHECK (Solo falta revisar el paso de los switchs)

        file_name, _ = QFileDialog.getOpenFileName(
            self, "Abrir Proyecto", "", "Archivo de Proyecto (*.json)"
        )
        if not file_name:
            return None
        try:
            project = self.file_manager.openFile(file_name)
            self._editor.setAssetsDirectory(project.assetsDirectory)
            if project.imageSize is not None:
                self._fontSizeBox.setCurrentText(f"{project.imageSize}")

            if self._toggleViewAction.isChecked():
                self._editor.setContent(project.content)
            else:
                self._editor.switchToTextView()
                self._editor.setContent(project.content)
                self._editor.switchToImageView()

        except ValueError as e:
            QMessageBox.critical(self, "Error", f"Error de archivo: {str(e)}")

        except ValidationError as e:
            QMessageBox.critical(self, "Error", f"El archivo no es válido o está corrupto")

        except Exception as e:
            QMessageBox.critical(
                self, "Error", f"No se pudo abrir el archivo: {str(e)}"
            )


    def onSaveFile(
        self,
    ):  # CHECK. Falta pasar la lógica de obtención del contenido a la clase del editor

        if self.file_manager.get_current_filename() is None:
            self.onSaveFileAs()
            return
        project = self._projectModel()
        try:
            self.file_manager.saveFile(project)
        except Exception as error:
            QMessageBox.critical(
                self, "Error", f"No se pudo guardar el archivo: {str(error)}"
            )

    def onSaveFileAs(
        self,
    ):  # CHECK. Falta pasar la lógica de obtención del contenido a la clase del editor

        project = self._projectModel()
        current_filename = self.file_manager.get_current_filename()
        new_filename = f"{current_filename if current_filename is not None else self.config.UNTITLED_DEFAULT_FILENAME}"
        new_filename: str = f"{new_filename}.json" if not new_filename.lower().endswith(".json") else new_filename
        file_name, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar Proyecto",
            new_filename,
            f"Archivo de Proyecto (*.{self.file_manager.get_file_extension()})",
        )
        if not file_name:
            return

        try:
            self.file_manager.saveFileAs(file_name, project)
        except Exception as error:
            QMessageBox.critical(
                self, "Error", f"No se pudo crear el archivo de proyecto: {str(error)}"
            )


    ### Se está guardando con .json
    def onExportPdf(self):
        
        current_filename = self.file_manager.get_current_filename()
        file_name, _ = QFileDialog.getSaveFileName(
            self,
            "Exportar a PDF",
            f"{current_filename if current_filename is not None else self.config.UNTITLED_DEFAULT_FILENAME}.pdf",
            "Documento PDF (*.pdf)",
        )
        if not file_name:
            return

        if not file_name.lower().endswith(".pdf"):
            file_name += ".pdf"

        # Forzar vista de imágenes antes de renderizar la hoja física
        if self._toggleViewAction.isChecked():
            self._toggleViewAction.setChecked(False)

        pdf_writer = QPdfWriter(file_name)
        pdf_writer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
        pdf_writer.setPageMargins(QMarginsF(0, 0, 0, 0))
        pdf_writer.setResolution(96)

        painter = QPainter()
        if not painter.begin(pdf_writer):
            QMessageBox.critical(self, "Error", "No se pudo activar el PDF.")
            return

        page_height = self._editor.page_height
        page_width = self._editor.page_width
        total_height = self._editor.document().size().height()
        total_pages = max(1, math.ceil(float(total_height) / page_height))

        for i in range(total_pages):
            if i > 0:
                pdf_writer.newPage()

            painter.save()
            painter.translate(0, -(i * page_height))
            painter.setClipRect(0, i * page_height, page_width, page_height)

            self._editor.document().drawContents(
                painter, QRectF(0, 0, page_width, total_height)
            )
            painter.restore()

        painter.end()
        QMessageBox.information(self, "Éxito", f"PDF generado exitosamente.")

    def onExportImage(self):
        file_name, _ = QFileDialog.getSaveFileName(
            self, "Exportar como Imagen", "untiled.png", "Imagen PNG (*.png)"
        )
        if not file_name:
            return

        base_path, _ = os.path.splitext(file_name)

        if self._toggleViewAction.isChecked():
            self._toggleViewAction.setChecked(False)

        page_height = self._editor.page_height
        page_width = self._editor.page_width
        total_height = self._editor.document().size().height()
        total_pages = max(1, math.ceil(float(total_height) / page_height))

        for i in range(total_pages):
            pixmap = QPixmap(page_width, page_height)
            # pixmap.fill(Qt.GlobalColor.white)
            pixmap.fill(Qt.GlobalColor.transparent)

            painter = QPainter(pixmap)
            painter.save()
            painter.translate(0, -(i * page_height))
            painter.setClipRect(0, i * page_height, page_width, page_height)

            self._editor.document().drawContents(
                painter, QRectF(0, 0, page_width, total_height)
            )
            painter.restore()
            painter.end()

            page_file_name = f"{base_path}_{i + 1}.png"
            pixmap.save(page_file_name, "PNG")

        QMessageBox.information(
            self, "Éxito", f"Se han exportado {total_pages} imágenes individuales."
        )

    ##
    ## Acá veré cómo funciona lo del drag
    ##
    def _open_symbols_window(self):
        if self._symbol_collection_editor is None:
            self._symbol_collection_editor = SymbolSelectorWindow(self._symbol_mapper, self)
            self._symbol_collection_editor.symbols_changed.connect(self.onSymbolsChanged)
            self._symbol_collection_editor.show()
        else:
            self._symbol_collection_editor.show()
            # self._symbol_collection_editor.destroyed.connect(self._on_destroyed_symbol_selector)
    def _on_destroyed_symbol_selector(self):
        self._symbol_collection_editor = None
    ##
    ## Hasta acá vi cómo funciona lo del drag
    ##

    def onChangeSymbols(self):

  
        files = QFileDialog.getOpenFileNames(
            self,
            "Selecciona los símbolos",
            self._editor.getAssetsDirectory()
        )
        if files:
            print(files)
            dir = os.path.dirname(files[0][0])
            print(dir)
        else:
            return

        
        # directory = QFileDialog.getExistingDirectory(
        #     self,
        #     "Seleccionar Directorio de Símbolos",
        #     self._editor.getAssetsDirectory(),
        #     QFileDialog.Option.ShowDirsOnly | QFileDialog.Option.DontResolveSymlinks,
        # )
        # if directory:
        #     self._editor.setAssetsDirectory(directory)
        #     QMessageBox.information(
        #         self, "Set Cambiado", f"Se han cargado los símbolos desde: {directory}"
        #     )

    def onChangeDirectory(self):
        directory = QFileDialog.getExistingDirectory(
            self,
            "Seleccionar Directorio de Símbolos",
            self._editor.getAssetsDirectory(),
            QFileDialog.Option.ShowDirsOnly | QFileDialog.Option.DontResolveSymlinks,
        )
        if directory:
            self._editor.setAssetsDirectory(directory)
            QMessageBox.information(
                self, "Set Cambiado", f"Se han cargado los símbolos desde: {directory}"
            )

    def _tutorial_window(self):

        QMessageBox().information(
        # mensaje = QMessageBox.information(
            self, 
            "Instrucciones", 
            textwrap.dedent("""
            <b>Elegir símbolos</b><br>
            1. Presiona 'Elegir Símbolos'.<br>
            2. Elige la carpeta donde tienes tus imágenes.<br>
            * Cada imagen debe tener como nombre la letra que representa en minúscula. Por ejemplo 'a.png', 'b.jpg'.<br>
            <br>
            <b>Cambiar modo de vista</b><br>

            Presiona el botón 'Modo Texto' o 'Modo Símbolos' para cambiar el modo en que se muestran los símbolos en la hoja.<br>
            """)
        )

    
    def _create_actions(self):

        # Abrir
        self._openAction = QAction("Abrir...", self)
        self._openAction.setShortcut(QKeySequence.StandardKey.Open)
        self._openAction.triggered.connect(self.onOpenFile)
        # Guardar / Guardar como
        self._saveAction = QAction("Guardar", self)
        self._saveAction.setShortcut(QKeySequence.StandardKey.Save)
        self._saveAction.triggered.connect(self.onSaveFile)
        self._saveAsAction = QAction("Guardar como...", self)
        self._saveAsAction.setShortcut(QKeySequence.StandardKey.SaveAs)
        self._saveAsAction.triggered.connect(self.onSaveFileAs)

        # Exportar
        self._exportPdfAction = QAction("Exportar PDF", self)
        self._exportPdfAction.triggered.connect(self.onExportPdf)
        self._exportImageAction = QAction("Exportar PNG", self)
        self._exportImageAction.triggered.connect(self.onExportImage)

        # Configuración / Vistas
        self._changeDirAction = QAction("Elegir Símbolos", self)
        self._changeDirAction.triggered.connect(self._open_symbols_window)
        # self._changeDirAction.triggered.connect(self.onChangeSymbols)
        # self._changeDirAction.triggered.connect(self.onChangeDirectory)


        self._toggleViewAction = QAction("Modo Símbolos", self)
        self._toggleViewAction.setCheckable(True)
        self._toggleViewAction.toggled.connect(self.onToggleViewChanged)


        # Ventana de ayuda
        self._tutorialAction = QAction("Instrucciones", self)
        self._tutorialAction.triggered.connect(self._tutorial_window)        

    def _create_toolbar(self):
        toolbar = QToolBar("Barra de Herramientas Main", self)
        self.addToolBar(toolbar)

        # Tamaño de Fuente
        toolbar.addWidget(QLabel(" Tamaño: ", self))
        self._fontSizeBox = self._build_font_size_combobox()
        toolbar.addWidget(self._fontSizeBox)
        toolbar.addSeparator()

        # Configuración y Modos
        toolbar.addAction(self._changeDirAction)
        toolbar.addSeparator()
        toolbar.addAction(self._toggleViewAction)
        self._mainToolBar = toolbar

        # Tutorial e instrucciones
        self._mainToolBar = toolbar

    def _create_menu_bar(self):
        file_menu = self.menuBar().addMenu("&Archivo")
        file_menu.addAction(self._openAction)
        file_menu.addAction(self._saveAction)
        file_menu.addAction(self._saveAsAction)
        file_menu.addSeparator()
        file_menu.addAction(self._exportPdfAction)
        file_menu.addAction(self._exportImageAction)

        file_menu = self.menuBar().addMenu("&Ayuda")
        file_menu.addAction(self._tutorialAction)

    def _build_font_size_combobox(self) -> QComboBox:
        box = QComboBox(self)
        sizes = [
            "1", "2", "4", "6", "8", "10", "12", "14", "18", "22", "24",
            "28", "32", "36", "40", "44", "48", "52", "56", "60", "66", "72", "80", "88", "96"
        ]
        box.addItems(sizes)
        box.setCurrentText("40")
        box.setEditable(True)
        box.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        
        box.lineEdit().returnPressed.connect(self.onFontSizeChanged)
        box.currentIndexChanged.connect(self.onFontSizeChanged)
        return box

    def _projectModel(self) -> ProjectModel:   # Auxiliar, crea el objeto de guardado

        was_in_images_mode = not self._toggleViewAction.isChecked()
        if was_in_images_mode:
            self._editor.switchToTextView()
        project = ProjectModel(
            version = self.config.APP_VERSION,
            content = self._editor.toPlainText(),
            imageSize = int(self._fontSizeBox.currentText()),
            assetsDirectory = self._editor.getAssetsDirectory(),
        )
        if was_in_images_mode:
            self._editor.switchToImageView()
        return project
