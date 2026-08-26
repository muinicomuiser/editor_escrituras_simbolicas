import os
import math
import textwrap
from time import sleep
from PySide6 import QtCore
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
    QAbstractTextDocumentLayout,
    QAction,
    QKeySequence,
    QPalette,
    QPdfWriter,
    QPainter,
    QPixmap,
)
from PySide6.QtCore import QCoreApplication, QEventLoop, QSize, Qt, QMarginsF, QRectF
from pydantic import ValidationError

from modules.config.config import Config
from modules.editor_widget import EditorWidget
from modules.persistence.file_manager import FileManager
from modules.shared.models.project_model import ProjectModel
from modules.symbols.symbol_selector_widget import SymbolSelectorWindow
from modules.symbols.symbol_mapper import SymbolMapper
from modules.utils.logger import get_logger

class MainWindow(QMainWindow):
    def __init__(self, config: Config, parent=None):
        self.logger = get_logger(self.__class__.__name__)
        super().__init__(parent)
        self.config = config
        self.setObjectName("MainWindow")

        self.setWindowTitle(self.config.MAIN_WINDOW_TITLE)
        self.resize(self.config.WIDTH, self.config.HEIGHT)
        self.setAcceptDrops(False)

        # Contenedor central
        self.container = QWidget(self)
        self.container.setObjectName("MainWidget")
        self.setCentralWidget(self.container)
        self.main_layout = QHBoxLayout(self.container)

        # Symbol Mapper para inyectar en editor y ventana de colecciones
        self._symbol_mapper = SymbolMapper()

        # Editor
        self._editor = EditorWidget(self.config, self._symbol_mapper, self)
        self.main_layout.addWidget(self._editor)
        self.main_layout.setAlignment(self._editor, Qt.AlignmentFlag.AlignHCenter)
        self.main_layout.setContentsMargins(0, 20, 0, 20)

        # Dependencia de persistencia
        self.file_manager = FileManager()
        self._editor.textChanged.connect(self.file_manager.set_to_unsaved)

        # Prueba de ventana de drag y drop
        self._symbol_collection_editor = SymbolSelectorWindow(self._symbol_mapper, self)
        self._symbol_collection_editor.symbols_changed.connect(self.onSymbolsChanged)

        # comandos de usuario (QActions)
        self._create_actions()

        # barra de herramientas
        self._create_toolbar()

        # menú superior
        self._create_menu_bar()

        # Logger
        self.logger = get_logger(self.__class__.__name__)
        self.logger.info(f"Módulo Iniciado")           

    def onToggleViewChanged(self, checked: bool):  # CHECK
        # print(self._toggleViewAction.isChecked())
        if checked:
            self._toggleViewAction.setText("Modo Texto")
            self._editor.switchToTextView()
        else:
            self._toggleViewAction.setText("Modo Símbolos")
            self._editor.switchToImageView()

    ## TODO: Agregar una función que rerenderice las imágenes, sin tener que pasar a texto y a imagen nuevamente
    def onFontSizeChanged(self):

        current_str = self._fontSizeBox.currentText()
        new_size_str = current_str.replace(",", ".").split(".")[0]
        if not new_size_str or not new_size_str.isnumeric():
            self.logger.info(f"Tamaño de fuente no válido: {new_size_str}")
            self._fontSizeBox.setCurrentText(str(self._editor.font().pointSize()))
        elif new_size_str == str(self._editor.font().pointSize()):
            pass
        else:
            if current_str != new_size_str:
                self._fontSizeBox.setCurrentText(new_size_str)
            new_size = int(
                float(new_size_str)
            )  # Falta manejar excepciones o casos en que sea un str que no pueda convertirse a int
            self._editor.setFontSize(new_size)

            self.updateSymbolsView()
        self._editor.setFocus()

    def updateSymbolsView(self):
        if not self._toggleViewAction.isChecked():
            self._editor.switchToTextView()
            self._editor.switchToImageView()        

    def onSymbolsChanged(self):
        self.updateSymbolsView()
        self.file_manager.set_to_unsaved()

    def onOpenFile(self):  ## CHECK (Solo falta revisar el paso de los switchs)

        file_name, _ = QFileDialog.getOpenFileName(
            self, "Abrir Proyecto", "", "Archivo de Proyecto (*.json)"
        )
        if not file_name:
            return None
        try:
            project = self.file_manager.openFile(file_name)
            collection = self._symbol_collection_editor.select_collection_by_name(
                project.collectionName
            )
            if project.imageSize is not None:
                self._fontSizeBox.setCurrentText(f"{project.imageSize}")
                self._editor.setFontSize(project.imageSize)

            if not collection:
                self.logger.warning(f"No se encontró la colección '{project.collectionName}'")
                QMessageBox.information(self, "Proyecto sin símbolos", f"No se encontró la colección de símbolos '{project.collectionName}' del proyecto. Puedes elegir una o crear una nueva en 'Elegir Símbolos'")

            if self._toggleViewAction.isChecked():
                self._editor.setContent(project.content)
            else:
                self._editor.switchToTextView()
                self._editor.setContent(project.content)
                self._editor.switchToImageView()
            self.logger.info(f"Proyecto abierto: '{file_name}'")
        except ValueError as e:
            self.logger.error(f"No se pudo abrir el archivo: {str(e)}")
            QMessageBox.critical(self, "Error", f"El archivo no es válido o está corrupto: {file_name}")

        except ValidationError as e:
            self.logger.error(f"El archivo no es válido o está corrupto: {file_name}")
            QMessageBox.critical(
                self, "Error", f"El archivo no es válido o está corrupto"
            )

        except Exception as e:
            self.logger.error(f"No se pudo abrir el archivo: {file_name}")
            QMessageBox.critical(
                self, "Error", f"No se pudo abrir el archivo: {str(e)}"
            )
        self.file_manager.set_to_saved()

    def onSaveFile(
        self,
    ):  # CHECK. Falta pasar la lógica de obtención del contenido a la clase del editor
        current_filename = self.file_manager.get_current_filename()
        if current_filename is None:
            self.onSaveFileAs()
            return
        project = self._projectModel()
        try:
            self.file_manager.saveFile(project)
            self.logger.info(f"Proyecto guardado: '{current_filename}'")
        except Exception as error:
            QMessageBox.critical(
                self, "Error", f"No se pudo guardar el archivo: {str(error)}"
            )
        self.file_manager.set_to_saved()
    def onSaveFileAs(
        self,
    ):  # CHECK. Falta pasar la lógica de obtención del contenido a la clase del editor

        project = self._projectModel()
        current_filename = self.file_manager.get_current_filename()
        new_filename = f"{current_filename if current_filename is not None else self.config.UNTITLED_DEFAULT_FILENAME}{self.file_manager.get_file_extension()}"
        file_name, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar Proyecto",
            new_filename,
            f"Archivo de Proyecto (*{self.file_manager.get_file_extension()})",
        )
        if not file_name:
            return

        try:
            self.file_manager.saveFileAs(file_name, project)
            self.logger.info(f"Proyecto guardado como: '{file_name}'")
        except Exception as error:
            QMessageBox.critical(
                self, "Error", f"No se pudo crear el archivo de proyecto: {str(error)}"
            )
        self.file_manager.set_to_saved()

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

        if self._toggleViewAction.isChecked():
            self._toggleViewAction.setChecked(False)

        self._editor.prepare_for_export(factor=4)

        page_height = self._editor.page_height
        page_width = self._editor.page_width

        pdf_writer = QPdfWriter(file_name)
        pdf_writer.setPageSize(QSize(page_width, page_height))
        pdf_writer.setPageMargins(QMarginsF(0, 0, 0, 0))
        pdf_writer.setResolution(72)  # 72 DPI es el estándar nativo de puntos para PDF
        
        painter = QPainter()
        if not painter.begin(pdf_writer):
            QMessageBox.critical(self, "Error", "No se pudo activar el PDF.")
            self._editor.restore_after_export()
            return

        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

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
        self._editor.restore_after_export()

    def onExportImage(self):
        file_name, _ = QFileDialog.getSaveFileName(
            self,
            "Exportar como Imagen",
            f"{self.file_manager.get_current_filename()}.png",
            "Imagen PNG (*.png)",
        )
        if not file_name:
            return

        base_path, _ = os.path.splitext(file_name)

        image_mode = not self._toggleViewAction.isChecked()
        sufix = "imagen" if image_mode else "texto"

        if image_mode:
            self._editor.prepare_for_export(factor=4)

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
            if image_mode:
                self._editor.document().drawContents(
                    painter, QRectF(0, 0, page_width, total_height)
                )
            else:
                ctx = QAbstractTextDocumentLayout.PaintContext()
                ctx.palette.setColor(QPalette.ColorGroup.All, QPalette.ColorRole.Text, "#333333")
                ctx.clip = QRectF(0, 0, page_width, total_height)
                self._editor.document().documentLayout().draw(painter, ctx)
            painter.restore()
            painter.end()

            page_file_name = f"{base_path}_{i + 1}_{sufix}.png"
            pixmap.save(page_file_name, "PNG")

        if image_mode:
            self._editor.prepare_for_export(factor=4)

    def _open_symbols_window(self):
        self._symbol_collection_editor.show()



    def closeEvent(self, event):
        if not self.file_manager.is_saved():
            button = QMessageBox.question(
                self,
                "Cambios no guardados",
                "Hay cambios sin guardar. ¿Quieres guardarlos antes de cerrar?",
                buttons=QMessageBox.StandardButton.No
                | QMessageBox.StandardButton.Yes
                | QMessageBox.StandardButton.Cancel,
            )            
            if button == QMessageBox.StandardButton.Cancel:
                event.ignore()

                return
            elif button == QMessageBox.StandardButton.Yes:
                self.onSaveFile()
            elif button == QMessageBox.StandardButton.No:
                pass
        event.accept()
        self.logger.info("Aplicación cerrada")
        return super().closeEvent(event)

    def _about_window(self):

        QMessageBox().information(
            self,
            "Información",
            textwrap.dedent("""
            <b>Sobre el editor de escrituras simbólicas</b><br>
            <br>
            Este programa fue realizado a partir del trabajo artístico de Valentina Morales (IG: @duerme_volantina), asociado a sus reflexiones sobre la escritura y las cosas pequeñas del mundo.<br>

            Autor: Nicolás Donoso (IG: @niconicodonoso)
            """)
        )

    def _tutorial_window(self):

        QMessageBox().information(
            self,
            "Instrucciones",
            textwrap.dedent("""
            <b>Elegir símbolos</b><br>
            Presiona 'Elegir Símbolos'.<br>
            Se abrirá una ventana que te permite abrir, crear y modificar colecciones de símbolos, arrastrando imágenes a cada letra..<br>
            <br>
            <b>Cambiar modo de vista</b><br>

            Presiona el botón 'Modo Texto' o 'Modo Símbolos' para cambiar el modo en que se muestran los símbolos en la hoja.<br>
            """),
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

        self._toggleViewAction = QAction("Modo Símbolos", self)
        self._toggleViewAction.setCheckable(True)
        self._toggleViewAction.toggled.connect(self.onToggleViewChanged)

        # Ventana de ayuda
        self._tutorialAction = QAction("Instrucciones", self)
        self._tutorialAction.triggered.connect(self._tutorial_window)
        self._aboutAction = QAction("Sobre el editor", self)
        self._aboutAction.triggered.connect(self._about_window)

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
        file_menu.addAction(self._aboutAction)

    def _build_font_size_combobox(self) -> QComboBox:
        box = QComboBox(self)
        sizes = [
            "1",
            "2",
            "4",
            "6",
            "8",
            "10",
            "12",
            "14",
            "18",
            "22",
            "24",
            "28",
            "32",
            "36",
            "40",
            "44",
            "48",
            "52",
            "56",
            "60",
            "66",
            "72",
            "80",
            "88",
            "96",
        ]
        init_size = "60"
        box.addItems(sizes)
        box.setObjectName("FontSizeBox")
        box.setCurrentText(init_size)
        box.setEditable(True)
        box.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)

        box.lineEdit().returnPressed.connect(self.onFontSizeChanged)
        box.currentIndexChanged.connect(self.onFontSizeChanged)
        return box

    def _projectModel(self) -> ProjectModel:  # Auxiliar, crea el objeto de guardado

        was_in_images_mode = not self._toggleViewAction.isChecked()
        if was_in_images_mode:
            self._editor.switchToTextView()
        project = ProjectModel(
            version=self.config.APP_VERSION,
            content=self._editor.toPlainText(),
            imageSize=int(self._fontSizeBox.currentText()),
            collectionName=self._symbol_collection_editor.get_current_collection_name(),
        )
        if was_in_images_mode:
            self._editor.switchToImageView()
        return project
