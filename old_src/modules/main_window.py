import os
import math
from PySide6.QtWidgets import (
    QComboBox,
    QFontComboBox,
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QToolBar,
    QLabel,
    QSpinBox,
    QFileDialog,
    QMessageBox,
)
from PySide6.QtGui import QAction, QFontMetrics, QIntValidator, QKeySequence, QPageSize, QPdfWriter, QPainter, QPixmap
from PySide6.QtCore import Qt, QMarginsF, QRectF

from modules.config.config import Config
from modules.editor_widget import EditorWidget
from modules.file_manager import FileManager


class MainWindow(QMainWindow):
    def __init__(self, config: Config, parent=None):
        super().__init__(parent)
        self.config = config



        self.container = QWidget(self)
        self.main_layout = QHBoxLayout(self.container)


        self.m_editor = EditorWidget(self)
        self.main_layout.addWidget(self.m_editor)
        self.main_layout.setAlignment(self.m_editor, Qt.AlignmentFlag.AlignHCenter)
        self.main_layout.setContentsMargins(0, 20, 0, 20)

        self.file_manager = FileManager()
        self.actual_file_name = None
        self.m_editor.textChanged.connect(self.file_manager.set_to_unsaved)   # Conecta señales entre componentes     


        self.setCentralWidget(self.container)
        self.__init_toolbar()
        self.setWindowTitle("Editor de Texto con Imágenes")
        self.resize(self.config.WIDTH, self.config.HEIGHT)
        # self.show()

    def onToggleViewChanged(self, checked: bool):
        if checked:
            self.m_toggleViewAction.setText("Modo Imágenes")
            self.m_editor.switchToTextView()
        else:
            self.m_toggleViewAction.setText("Modo Texto")
            self.m_editor.switchToImageView()

    def onImageSizeChanged(self):
        new_size_str = self.m_font_size.currentText()
        if not new_size_str:
            self.m_font_size.setCurrentText(str(self.m_editor.font().pointSize()))
        elif new_size_str == str(self.m_editor.font().pointSize()):
            pass
        else:
            new_size = int(new_size_str)

            fuente = self.m_editor.font()
            fuente.setPointSize(int(new_size))
            fuente.setWordSpacing(float(new_size))
            self.m_editor.setFont(fuente)

            font_metrics = QFontMetrics(self.m_editor.font())
            # print(font_metrics.size(Qt.TextSingleLine, " ").width())
            font_width = font_metrics.horizontalAdvance("W")

            nueva_escala = float(font_width) / 24.0
            self.m_editor.setImageScale(nueva_escala)


            if not self.m_toggleViewAction.isChecked():
                self.m_editor.switchToTextView()
                self.m_editor.switchToImageView()


        self.m_editor.setFocus()


    # def onImageSizeChanged(self):
    #     new_size_str = self.m_font_size.currentText()
    #     if not new_size_str:
    #         self.m_font_size.setCurrentText(str(self.m_editor.font().pointSize()))
    #     elif new_size_str == str(self.m_editor.font().pointSize()):
    #         pass
    #     else:
    #         new_size = int(new_size_str)
    #         # new_size = int(size_str)
    #         # 1. Escala proporcional basada en 32px
    #         nueva_escala = float(new_size) / 32.0
    #         self.m_editor.setImageScale(nueva_escala)

    #         # 2. Re-dimensionamiento de la tipografía y el espaciado
    #         fuente = self.m_editor.font()
    #         fuente.setPointSize(int(new_size * 0.75))
    #         fuente.setWordSpacing(float(new_size))
    #         self.m_editor.setFont(fuente)

    #         # 3. Forzar reconstrucción si está en modo imágenes
    #         if not self.m_toggleViewAction.isChecked():
    #             self.m_editor.switchToTextView()
    #             self.m_editor.switchToImageView()
    #     # font_metrics = QFontMetrics(self.m_editor.font())
    #     # print(font_metrics.size(Qt.TextSingleLine, " ").width())
    #     # print(font_metrics.horizontalAdvance(" "))
    #     self.m_editor.setFocus()

    def onOpenFile(self):
        file = self.file_manager.openFile(self.window())

        if file is None:
            return
        
        text_content, font_size, saved_dir, file_name = file
        self.m_editor.changeAssetsDirectory(saved_dir)
        self.m_sizeSpinner.setValue(font_size)

        self.m_editor.clear()
        if self.m_toggleViewAction.isChecked():
            self.m_editor.setPlainText(text_content)
        else:
            self.m_editor.switchToTextView()
            self.m_editor.setPlainText(text_content)
            self.m_editor.switchToImageView()

        if file_name is not None:
            self.actual_file_name = file_name
            self.file_manager.set_to_saved()
             


    def onSaveFile(self):
        if self.actual_file_name is None:
            self.onSaveFileAs()
        was_in_images_mode = not self.m_toggleViewAction.isChecked()
        if was_in_images_mode:
            self.m_editor.switchToTextView()
        content_to_save = self.m_editor.toPlainText()
        project_dict = {
            "version": "1.0",
            "content": content_to_save,
            "imageSize": self.m_sizeSpinner.value(),
            "assetsDirectory": self.m_editor.getAssetsDirectory(),
        }
        if was_in_images_mode:
            self.m_editor.switchToImageView()
        self.file_manager.saveFile(self.window(), project_dict, self.actual_file_name)
        
    def onSaveFileAs(self):
        was_in_images_mode = not self.m_toggleViewAction.isChecked()
        if was_in_images_mode:
            self.m_editor.switchToTextView()
        content_to_save = self.m_editor.toPlainText()
        project_dict = {
            "version": "1.0",
            "content": content_to_save,
            "imageSize": self.m_sizeSpinner.value(),
            "assetsDirectory": self.m_editor.getAssetsDirectory(),
        }
        if was_in_images_mode:
            self.m_editor.switchToImageView()
        file_name = self.file_manager.saveFileAs(self.window(), project_dict)
        self.actual_file_name = file_name

    def onExportPdf(self):
        file_name, _ = QFileDialog.getSaveFileName(
            self, "Exportar a PDF","untiled.pdf", "Documento PDF (*.pdf)"
        )
        if not file_name:
            return

        if not file_name.lower().endswith(".pdf"):
            file_name += ".pdf"

        # Forzar vista de imágenes antes de renderizar la hoja física
        if self.m_toggleViewAction.isChecked():
            self.m_toggleViewAction.setChecked(False)

        pdf_writer = QPdfWriter(file_name)
        pdf_writer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
        pdf_writer.setPageMargins(QMarginsF(0, 0, 0, 0))
        pdf_writer.setResolution(96)

        painter = QPainter()
        if not painter.begin(pdf_writer):
            QMessageBox.critical(self, "Error", "No se pudo activar el PDF.")
            return

        page_height = 1123
        page_width = 794
        total_height = self.m_editor.document().size().height()
        total_pages = max(1, math.ceil(float(total_height) / page_height))

        for i in range(total_pages):
            if i > 0:
                pdf_writer.newPage()

            painter.save()
            painter.translate(0, -(i * page_height))
            painter.setClipRect(0, i * page_height, page_width, page_height)

            self.m_editor.document().drawContents(
                painter, QRectF(0, 0, page_width, total_height)
            )
            painter.restore()

        painter.end()
        QMessageBox.information(
            self, "Éxito", f"PDF generado con {total_pages} páginas."
        )

    def onExportImage(self):
        file_name, _ = QFileDialog.getSaveFileName(
            self, "Exportar como Imagen", "untiled.png", "Imagen PNG (*.png)"
        )
        if not file_name:
            return

        base_path, _ = os.path.splitext(file_name)

        if self.m_toggleViewAction.isChecked():
            self.m_toggleViewAction.setChecked(False)

        page_height = 1123
        page_width = 794
        total_height = self.m_editor.document().size().height()
        total_pages = max(1, math.ceil(float(total_height) / page_height))

        for i in range(total_pages):
            pixmap = QPixmap(page_width, page_height)
            # pixmap.fill(Qt.GlobalColor.white)
            pixmap.fill(Qt.GlobalColor.transparent)

            painter = QPainter(pixmap)
            painter.save()
            painter.translate(0, -(i * page_height))
            painter.setClipRect(0, i * page_height, page_width, page_height)

            self.m_editor.document().drawContents(
                painter, QRectF(0, 0, page_width, total_height)
            )
            painter.restore()
            painter.end()

            page_file_name = f"{base_path}_{i + 1}.png"
            pixmap.save(page_file_name, "PNG")

        QMessageBox.information(
            self, "Éxito", f"Se han exportado {total_pages} imágenes individuales."
        )

    def onChangeDirectory(self):
        directory = QFileDialog.getExistingDirectory(
            self,
            "Seleccionar Directorio de Símbolos",
            self.m_editor.getAssetsDirectory(),
            QFileDialog.Option.ShowDirsOnly | QFileDialog.Option.DontResolveSymlinks,
        )
        if directory:
            self.m_editor.changeAssetsDirectory(directory)
            QMessageBox.information(
                self, "Set Cambiado", f"Se han cargado los símbolos desde: {directory}"
            )

    # ---- BARRA DE HERRAMIENTAS ----
    def __init_toolbar(self):
        self.m_mainToolBar = QToolBar("Barra de Herramientas", self)
        self.addToolBar(self.m_mainToolBar)

        # Abrir
        self.m_openAction = QAction("Abrir", self)
        # self.m_mainToolBar.addAction(self.m_openAction)
        self.m_openAction.triggered.connect(self.onOpenFile)
        open_key_combination = QKeySequence.fromString("Ctrl+O")
        self.m_openAction.setShortcut(open_key_combination)

        # Guardar
        self.m_saveAsAction = QAction("Guardar como...", self)
        # self.m_mainToolBar.addAction(self.m_saveAction)
        self.m_saveAsAction.triggered.connect(self.onSaveFileAs)

        self.m_saveAction = QAction("Guardar", self)
        # self.m_mainToolBar.addAction(self.m_saveAction)
        self.m_saveAction.triggered.connect(self.onSaveFile)
        save_key_combination = QKeySequence.fromString("Ctrl+S")
        self.m_saveAction.setShortcut(save_key_combination)

        self.m_mainToolBar.addSeparator()

        # Exportar PDF
        self.m_exportPdfAction = QAction("Exportar PDF", self)
        # self.m_mainToolBar.addAction(self.m_exportPdfAction)
        self.m_exportPdfAction.triggered.connect(self.onExportPdf)

        # Exportar Imagen
        self.m_exportImageAction = QAction("Exportar Imagen", self)
        # self.m_mainToolBar.addAction(self.m_exportImageAction)
        self.m_exportImageAction.triggered.connect(self.onExportImage)

        self.m_mainToolBar.addSeparator()

        # Selector de Tamaño de Fuente
        size_label = QLabel(self)
        # size_label = QLabel(" Tamaño: ", self)
        self.m_mainToolBar.addWidget(size_label)

        # self.m_sizeSpinner = QSpinBox(self)
        # self.m_sizeSpinner.setRange(16, 128)
        # self.m_sizeSpinner.setValue(48)
        # self.m_sizeSpinner.setSuffix(" px")
        # self.m_mainToolBar.addWidget(self.m_sizeSpinner)
        # self.m_sizeSpinner.valueChanged.connect(self.onImageSizeChanged)

        self.m_font_size = QComboBox(self)
        self.m_font_size.addItems(["1", "2", "4", "6", "8", "10", "12", "14", "18", "22", "24", "28", "32", "36", "40", "44", "48", "52", "56", "60", "66", "72", "80", "88", "96"])
        self.m_font_size.setCurrentText("40")
        self.m_font_size.setEditable(True)
        self.m_font_size.lineEdit().returnPressed.connect(self.onImageSizeChanged)
        self.m_font_size.currentIndexChanged.connect(self.onImageSizeChanged)
        self.m_font_size.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        # self.m_font_size.valueChanged.connect(self.onImageSizeChanged)
        # # validador = QIntValidator(1, 200, self)
        # # self.m_font_size.setValidator(validador)
        # # self.m_font_size.setSuffix(" px")
        self.m_mainToolBar.addWidget(self.m_font_size)
      

        self.m_mainToolBar.addSeparator()

        # Cambiar Set
        self.m_changeDirAction = QAction("Cambiar Set", self)
        self.m_mainToolBar.addAction(self.m_changeDirAction)
        self.m_changeDirAction.triggered.connect(self.onChangeDirectory)

        self.m_mainToolBar.addSeparator()

        # Alternar Vista
        self.m_toggleViewAction = QAction("Modo Texto", self)
        self.m_toggleViewAction.setCheckable(True)
        self.m_mainToolBar.addAction(self.m_toggleViewAction)
        self.m_toggleViewAction.toggled.connect(self.onToggleViewChanged)

        menu = self.menuBar()

        file_menu = menu.addMenu("&Archivo")
        file_menu.addAction(self.m_openAction)
        file_menu.addAction(self.m_saveAction)
        file_menu.addAction(self.m_saveAsAction)
        file_menu.addAction(self.m_exportPdfAction)
        file_menu.addAction(self.m_exportImageAction)