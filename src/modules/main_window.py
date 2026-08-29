import json
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
    QAbstractTextDocumentLayout,
    QAction,
    QKeySequence,
    QPalette,
    QPdfWriter,
    QPainter,
    QPixmap,
)
from PySide6.QtCore import QBuffer, QByteArray, QIODevice, QSize, Qt, QMarginsF, QRectF
from pydantic import ValidationError

from modules.config.config import Config
from modules.editor_widget import EditorWidget
from modules.persistence.projects_service import ProjectsService
from modules.persistence.file_service import FilesService
from modules.shared.models.project_model import ProjectModel
from modules.symbols.symbol_selector_widget import SymbolSelectorWindow
from modules.symbols.symbol_mapper import SymbolMapper
from modules.utils.logger import get_logger
from modules.exceptions.exceptions import StorageError

class MainWindow(QMainWindow):
    def __init__(self, config: Config, text_editor: EditorWidget, collections_editor: SymbolSelectorWindow, projects_service: ProjectsService, parent=None):
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
        self._editor = text_editor
        self._editor.setParent(self)
        self.main_layout.addWidget(self._editor)
        self.main_layout.setAlignment(self._editor, Qt.AlignmentFlag.AlignHCenter)
        self.main_layout.setContentsMargins(0, 20, 0, 20)

        # Dependencias de persistencia
        self.projects_service = projects_service
        self._editor.textChanged.connect(self.projects_service.set_to_unsaved)
        self.file_service = FilesService()

        # Prueba de ventana de drag y drop
        self._symbol_collection_editor = collections_editor
        self._symbol_collection_editor.setParent(self, Qt.WindowType.Window)
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
        if checked:
            self._toggleViewAction.setText("Modo Texto")
            self._editor.switchToTextView()
        else:
            self._toggleViewAction.setText("Modo Símbolos")
            self._editor.switchToImageView()

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
            )
            self._editor.setFontSize(new_size)

            self.updateSymbolsView()
        self._editor.setFocus()


    ## TODO: Una función que renderice las imágenes sin tener que pasar todo a modo texto antes
    def updateSymbolsView(self):
        """Actualiza el dibujo de los símbolos en el editor"""
        if not self._toggleViewAction.isChecked():
            self._editor.switchToTextView()
            self._editor.switchToImageView()        

    def onSymbolsChanged(self):
        self.updateSymbolsView()
        self.projects_service.set_to_unsaved()

    def onOpenFile(self):  ## CHECK (Solo falta revisar el paso de los switchs)
        """Abre un archivo de proyecto en la ruta señalada por el usuario y:
            - Carga su contenido en el editor       
            - Carga la colección de símbolos del archivo (si no la encuentra lo anuncia)        
            - Ajusta el tamaño de la fuente según el indicado en el archivo
        """
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Abrir Proyecto", "", "Archivo de Proyecto (*.json)"
        )
        if not file_name:
            return None
        try:
            project = self.projects_service.open(file_name)
            
            if project.imageSize:
                self._fontSizeBox.setCurrentText(f"{project.imageSize}")
                self._editor.setFontSize(project.imageSize)
            
            if project.collectionName:
                collection = self._symbol_collection_editor.select_collection_by_name(
                    project.collectionName
                )
                if not collection:
                    self.logger.warning(f"No se encontró la colección '{project.collectionName}'")
                    QMessageBox.information(self, "Colección de simbolos no encontrada", f"No se encontró la colección de símbolos '{project.collectionName}' del proyecto. Puedes elegir una o crear una nueva en 'Elegir Símbolos'")
            else:
                QMessageBox.information(self, "Proyecto sin símbolos", f"El proyecto no tiene una colección de símbolos definida. Puedes elegir una o crear una nueva en 'Elegir Símbolos'")
            self._editor.setContent(project.content)        
            self.logger.info(f"Proyecto abierto: '{file_name}'")

        except (ValidationError, json.JSONDecodeError) as e:
            self.logger.warning(f"El archivo no es válido o está corrupto: {file_name} | {e}")
            QMessageBox.critical(
                self, "Error de archivo", f"El archivo no es válido o está corrupto."
            )
        except FileNotFoundError as e:
            self.logger.warning(f"El archivo no es válido o está corrupto: {file_name} | {e}")
            QMessageBox.critical(
                self, "Error de archivo", f"Archivo no encontrado: {file_name}."
            )
        except StorageError as e:
            self.logger.error(f"No se pudo abrir el archivo {file_name} | {e}")
            QMessageBox.critical(
                self, "Error de acceso", f"No se pudo abrir el archivo: {file_name}. Verifica los permisos del sistema."
            )
        except Exception as e:
            self.logger.critical(f"Excepción no controlada al abrir archivo: {file_name} | {e}")
            QMessageBox.critical(
                self, "Error misterioso", "Ocurrió un error inesperado en la aplicación."
            )            
        self.projects_service.set_to_saved()

    def onSaveFile(
        self,
    ):
        current_filepath = self.projects_service.get_current_filepath()
        if current_filepath is None:
            self.onSaveFileAs()
            return
        project = self._generateProjectModel()
        try:
            self.projects_service.save(project)
            self.logger.info(f"Proyecto guardado: '{current_filepath}'")
            self.projects_service.set_to_saved()
        except StorageError as e:
            self.logger.error(f"No se pudo guardar el archivo {current_filepath} | {e}")            
            QMessageBox.critical(
                self, "Error al guardar", f"No se pudo guardar el archivo: {current_filepath}. \nVerifica que tengas espacio disponible en disco y permisos para guardar."
            )
        except Exception as e:
            self.logger.critical(f"Error inesperado al guardar el archivo: {current_filepath} | {e}")
            QMessageBox.critical(
                self, "Error misterioso", "Ocurrió un error inesperado en la aplicación al intentar guardar el archivo."
            ) 
    def onSaveFileAs(
        self,
    ):

        project = self._generateProjectModel()
        current_filename = self.projects_service.get_current_filename()
        new_filename = f"{current_filename if current_filename is not None else self.config.UNTITLED_DEFAULT_FILENAME}{self.projects_service.get_file_extension()}"
        file_name, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar Proyecto",
            new_filename,
            f"Archivo de Proyecto (*{self.projects_service.get_file_extension()})",
        )
        if not file_name:
            return
        try:
            self.projects_service.save(project, file_name)
            self.logger.info(f"Proyecto guardado como: '{file_name}'")
            self.projects_service.set_to_saved()
        except StorageError as e:
            self.logger.error(f"No se pudo guardar el archivo {file_name} | {e}")            
            QMessageBox.critical(
                self, "Error al guardar", f"No se pudo guardar el archivo: {file_name}. \nVerifica que tengas espacio disponible en disco y permisos para guardar."
            )
        except Exception as e:
            self.logger.critical(f"Error inesperado al guardar el archivo: {file_name} | {e}")
            QMessageBox.critical(
                self, "Error misterioso", "Ocurrió un error inesperado en la aplicación al intentar guardar el archivo."
            ) 

    def onExportPdf(self):

        current_filename = self.projects_service.get_current_filename()
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

        if not self._editor._is_text_view_mode:
            self._editor.prepare_for_export(factor=4)

        page_height = self._editor.page_height
        page_width = self._editor.page_width

        bytes_array = QByteArray()
        buffer = QBuffer(bytes_array)
        buffer.open(QIODevice.OpenModeFlag.WriteOnly)
        pdf_bytes_writer = QPdfWriter(buffer)
        pdf_bytes_writer.setPageSize(QSize(page_width, page_height))
        pdf_bytes_writer.setPageMargins(QMarginsF(0, 0, 0, 0))
        pdf_bytes_writer.setResolution(72)  # 72 DPI es el estándar nativo de puntos para PDF
        pdf_bytes_writer.setCreator(self.config.APP_NAME)
        
        painter = QPainter()
        if not painter.begin(pdf_bytes_writer):
            QMessageBox.critical(self, "Error", "No se pudo activar el PDF.")
            self._editor.restore_after_export()
            return

        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        total_height = self._editor.document().size().height()
        total_pages = max(1, math.ceil(float(total_height) / page_height))

        for i in range(total_pages):
            if i > 0:
                pdf_bytes_writer.newPage()

            painter.save()
            painter.translate(0, -(i * page_height))
            painter.setClipRect(0, i * page_height, page_width, page_height)
            if not self._editor._is_text_view_mode:
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
        buffer.close()
        try:
            self.file_service.save(file_name, bytes_array)
        except StorageError as e:
            self.logger.error(f"No se pudo exportar el PDF {file_name} | {e}")            
            QMessageBox.critical(
                self, "Error al exportar", f"No se pudo exportar el PDF: {file_name}. \nVerifica que tengas espacio disponible en disco y permisos para guardar."
            )
        except Exception as e:
            self.logger.critical(f"Error inesperado al exportar el PDF: {file_name} | {e}")
            QMessageBox.critical(
                self, "Error misterioso", "Ocurrió un error inesperado en la aplicación al intentar exportar el PDF."
            ) 
        finally:
            if not self._editor._is_text_view_mode:            
                self._editor.restore_after_export()

    def onExportImage(self):
        file_name, _ = QFileDialog.getSaveFileName(
            self,
            "Exportar como Imagen",
            f"{self.projects_service.get_current_filename()}.png",
            "Imagen PNG (*.png)",
        )
        if not file_name:
            return
        definition_multiplier = 6
        if not self._editor._is_text_view_mode:
            self._editor.prepare_for_export(factor=definition_multiplier)
        byte_array = QByteArray()
        buffer = QBuffer(byte_array)
        buffer.open(QIODevice.OpenModeFlag.WriteOnly)

        page_height = self._editor.page_height
        page_width = self._editor.page_width
        total_height = self._editor.document().size().height()


        ## Modo Horizontal
        ## Ordenar las páginas en un lienzo horizontal
        total_pages = max(1, math.ceil(float(total_height) / page_height))
        pixmap = QPixmap(page_width*definition_multiplier*total_pages, page_height*definition_multiplier)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.scale(definition_multiplier, definition_multiplier)
        for i in range(total_pages):
            painter.save()
            painter.translate(i*page_width, -(i*page_height))
            clip_rect = QRectF(0, page_height * i, page_width, page_height)
            painter.setClipRect(clip_rect)            
            if not self._editor._is_text_view_mode:
                self._editor.document().drawContents(
                    painter, clip_rect
                )
            else:
                ctx = QAbstractTextDocumentLayout.PaintContext()
                ctx.palette.setColor(QPalette.ColorGroup.All, QPalette.ColorRole.Text, "#333333")
                ctx.clip =clip_rect
                self._editor.document().documentLayout().draw(painter, ctx)
            painter.restore()
        painter.end()
        pixmap.save(buffer, "PNG") 
        buffer.close()
        try:
            self.file_service.save(file_name, byte_array)
        except StorageError as e:
            self.logger.error(f"No se pudo exportar el PDF {file_name} | {e}")            
            QMessageBox.critical(
                self, "Error al exportar", f"No se pudo exportar el PDF: {file_name}. \nVerifica que tengas espacio disponible en disco y permisos para guardar."
            )
        except Exception as e:
            self.logger.critical(f"Error inesperado al exportar el PDF: {file_name} | {e}")
            QMessageBox.critical(
                self, "Error misterioso", "Ocurrió un error inesperado en la aplicación al intentar exportar el PDF."
            ) 
        finally:
            if not self._editor._is_text_view_mode:            
                self._editor.restore_after_export()
        ## Modo Vertical
        ## Ordenar las páginas en un lienzo Vertical
        # pixmap = QPixmap(page_width*definition_multiplier, total_height*definition_multiplier)
        # pixmap.fill(Qt.GlobalColor.transparent)
        # painter = QPainter(pixmap)
        # painter.scale(definition_multiplier, definition_multiplier)
        # painter.save()
        # # painter.translate(0, 0)
        # painter.setClipRect(0, 0, page_width*definition_multiplier, total_height*definition_multiplier)
        # if not self._editor._is_text_view_mode:
        #     self._editor.document().drawContents(
        #         painter, QRectF(0, 0, page_width, total_height)
        #     )
        # else:
        #     ctx = QAbstractTextDocumentLayout.PaintContext()
        #     ctx.palette.setColor(QPalette.ColorGroup.All, QPalette.ColorRole.Text, "#333333")
        #     ctx.clip = QRectF(0, 0, page_width, total_height)
        #     self._editor.document().documentLayout().draw(painter, ctx)
        # painter.restore()
        # painter.end()
        # buffer.close()
        # pixmap.save(buffer, "PNG") # Retorna un bool
        # try:
        #   self.file_service.save(file_name, byte_array)
        # except StorageError as e:
        #     self.logger.error(f"No se pudo exportar el PDF {file_name} | {e}")            
        #     QMessageBox.critical(
        #         self, "Error al exportar", f"No se pudo exportar el PDF: {file_name}. \nVerifica que tengas espacio disponible en disco y permisos para guardar."
        #     )
        # except Exception as e:
        #     self.logger.critical(f"Error inesperado al exportar el PDF: {file_name} | {e}")
        #     QMessageBox.critical(
        #         self, "Error misterioso", "Ocurrió un error inesperado en la aplicación al intentar exportar el PDF."
        #     ) 
        # finally:
        #     if not self._editor._is_text_view_mode:            
        #         self._editor.restore_after_export()

        ## Modo Múltiples archivos
        ## Ordenar las páginas en un lienzo por página
        # total_pages = max(1, math.ceil(float(total_height) / page_height))
        # for i in range(total_pages):
        #     pixmap = QPixmap(page_width, page_height)
        #     # pixmap.fill(Qt.GlobalColor.white)
        #     pixmap.fill(Qt.GlobalColor.transparent)

        #     painter = QPainter(pixmap)
        #     painter.save()
        #     painter.translate(0, -(i * page_height))
        #     painter.setClipRect(0, i * page_height, page_width, page_height)
        #     if not self._editor._is_text_view_mode:
        #         self._editor.document().drawContents(
        #             painter, QRectF(0, 0, page_width, total_height)
        #         )
        #     else:
        #         ctx = QAbstractTextDocumentLayout.PaintContext()
        #         ctx.palette.setColor(QPalette.ColorGroup.All, QPalette.ColorRole.Text, "#333333")
        #         ctx.clip = QRectF(0, 0, page_width, total_height)
        #         self._editor.document().documentLayout().draw(painter, ctx)
        #     painter.restore()
        #     painter.end()

        #     page_file_name = f"{base_path}_{i + 1}_{sufix}.png"
        #     pixmap.save(page_file_name, "PNG")


    def _open_symbols_window(self):
        """Muestra la ventana del editor de colecciones de símbolos"""
        self._symbol_collection_editor.show()

    def closeEvent(self, event):
        if not self.projects_service.is_saved():
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
        self._symbol_collection_editor.close()
        event.accept()
        self.logger.info("Aplicación cerrada")
        return super().closeEvent(event)

    def _about_window(self):
        """Despliega una ventana informativa con datos de la"""

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
        """Despliega una ventana informativa con instrucciones de uso"""
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

    def _generateProjectModel(self) -> ProjectModel:  # Auxiliar, crea el objeto de guardado
        project = ProjectModel(
            version=self.config.APP_VERSION,
            content=self._editor.getContent(),
            imageSize=int(self._fontSizeBox.currentText()),
            collectionName=self._symbol_collection_editor.get_current_collection_name(),
        )
        return project
