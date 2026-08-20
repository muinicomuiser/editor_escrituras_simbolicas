import unicodedata

from PySide6.QtWidgets import QTextEdit
from PySide6.QtGui import (
    QFont,
    QFontMetrics,
    QKeyEvent,
    QInputMethodEvent,
    QFontDatabase,
    QPixmap,
    QTextBlockFormat,
    QTextCharFormat,
    QTextCursor,
    QTextDocument,
    QTextImageFormat,
    QTextFormat,
    QPainter,
    QPen,
    QColor,
    QTextOption,
)
from PySide6.QtCore import QRectF, QSize, QUrl, Qt, QSizeF
from modules.config.config import Config
from modules.symbols.symbol_mapper import SymbolMapper


class EditorWidget(QTextEdit):
    def __init__(self, config: Config, symbol_mapper: SymbolMapper, parent=None):
        super().__init__(parent)
        self.config = config
        self._symbol_mapper = symbol_mapper

        # razon = 300 // 96

        self.setObjectName("EditorWidget")
        self.page_height = self.config.HEIGHT
        self.page_width = self.config.WIDTH


        self._init_font_size = 60
        self._is_text_view_mode = False

        self.setAcceptRichText(True)
        self.setWordWrapMode(QTextOption.WrapMode.WrapAnywhere)
        self.setLineWrapMode(QTextEdit.LineWrapMode.FixedPixelWidth)
        self.setLineWrapColumnOrWidth(self.page_width)
        self.setAcceptDrops(False)

        ## Monospace cross platform
        fuente_original = QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont)
        fuente_original.setPointSize(self._init_font_size)
        fuente_original.setLetterSpacing(QFont.SpacingType.PercentageSpacing, 140)
        self.setFont(fuente_original)

        font_metrics = QFontMetrics(self.font())
        font_height = font_metrics.height()

        block_format = QTextBlockFormat()

        ### Sirve para setear la alineación del documento completo.
        ### El problema es que no logro que el pintado de las imágenes se ajuste a la alineación
        # block_format.setAlignment(Qt.AlignmentFlag.AlignCenter) #### Sirve para setear la alineación del documento completo.

        block_format.setLineHeight(float(font_height), 2)
        cursor = self.textCursor()
        cursor.setBlockFormat(block_format)
        self.setTextCursor(cursor)

        self.margin = 40
        self.innerPadding = 20
        self.doc = self.document()
        self.doc.setPageSize(QSizeF(self.page_width, self.page_height))
        self.page_gap = 0
        self._applyMargin()
        self.m_image_counter = 0

        # 3. Estilo Visual
        self._font_color = "#444444"
        self._background_color = "transparent"
        self.setStyleSheet(
            f"QTextEdit {{ background-color: {self._background_color}; color: {self._font_color}; }}"
        )
        self.setFixedWidth(self.page_width + self.innerPadding * 2)
        self._page_color = Qt.GlobalColor.white

    def setFontSize(self, fontSize: int):
        fuente = self.font()
        fuente.setPointSize(fontSize)
        fuente.setWordSpacing(0) ## Es el espaciado adicional al ancho de las letras al separar palabras.
        self.setFont(fuente)

    def set_page_color(self, color: Qt.GlobalColor):
        self._page_color = color
        self.update()

    # Método creado, por revisar
    def setContent(self, plain_text_content: str):
        self.clear()
        self.setPlainText(plain_text_content)

    def _to_clean_char(self, char: str):
        clean = char
        if clean not in ["ñ", "Ñ"]:
            nfkd = unicodedata.normalize("NFKD", char)
            clean = "".join([c for c in nfkd if not unicodedata.combining(c)])
        return clean.lower()

    def _insert_symbol_image(self, original_char: str, target_char: str):
        if not self._symbol_mapper.has_image(target_char):
            return False

        font_metrics = QFontMetrics(self.font())
        char_width = int(font_metrics.horizontalAdvance("W"))
        char_height = int(font_metrics.height())
        # char_width = int(font_metrics.horizontalAdvance("W") * self.m_imageScale)
        # char_height = int(font_metrics.height() * self.m_imageScale)

        # ID único de la imagen al tamaño (Caché)
        resource_id = f"sym_{target_char}_{char_width}_{char_height}"
        resource_url = QUrl(resource_id)

        doc = self.document()

        if not doc.resource(QTextDocument.ResourceType.ImageResource, resource_url):

            original_pixmap = self._symbol_mapper.get_pixmap(target_char)
            # original_pixmap = QPixmap(image_path)
            # image_path = self._symbol_mapper.get_image_path(target_char)
            # original_pixmap = QPixmap(image_path)
            scaled_pixmap = original_pixmap.scaled(
                char_width,
                char_height,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            canvas = QPixmap(char_width, char_height)
            canvas.fill(Qt.GlobalColor.transparent)

            # Dibujar la imagen escalada en el centro exacto del lienzo
            painter = QPainter(canvas)
            x = (char_width - scaled_pixmap.width()) // 2
            y = (char_height - scaled_pixmap.height()) // 2
            painter.drawPixmap(x, y, scaled_pixmap)
            painter.end()

            # Guardar el nuevo lienzo en los recursos en memoria del documento
            doc.addResource(
                QTextDocument.ResourceType.ImageResource, resource_url, canvas.toImage()
            )

        image_format = QTextImageFormat()
        image_format.setName(resource_url.toString())
        image_format.setWidth(char_width)
        image_format.setHeight(char_height)
        image_format.setVerticalAlignment(
            QTextCharFormat.VerticalAlignment.AlignBaseline
        )

        # 5. Propiedades para evitar que Qt fusione los bloques
        user_prop_char = int(QTextFormat.Property.UserProperty) + 1
        user_prop_id = int(QTextFormat.Property.UserProperty) + 2
        image_format.setProperty(user_prop_char, original_char)
        image_format.setProperty(user_prop_id, self.m_image_counter)
        self.m_image_counter += 1

        # 6. Insertar en el editor
        cursor = self.textCursor()
        formato_actual = self.currentCharFormat()
        formato_actual.setFont(self.font())
        cursor.setCharFormat(formato_actual)
        cursor.insertImage(image_format)
        self.setTextCursor(cursor)

        return True

    # Para eventos de tecla simple y vivas (como letras)
    def keyPressEvent(self, event: QKeyEvent):
        if self._is_text_view_mode or event.key() in (
            Qt.Key.Key_Backspace,
            Qt.Key.Key_Delete,
            Qt.Key.Key_Return,
            Qt.Key.Key_Enter,
        ):
            super().keyPressEvent(event)
            return
        text = event.text()
        if not text:
            super().keyPressEvent(event)
            return

        pressed_char = text[0]
        target_char = self._to_clean_char(pressed_char)

        # inserted_image = self._insert_image(pressed_char, target_char)
        inserted_image = self._insert_symbol_image(pressed_char, target_char)

        if not inserted_image:
            super().keyPressEvent(event)
            self.update()

    # Para eventos compuestos, como letras con tilde
    ## FALTA. Manejo de excepciones
    def inputMethodEvent(self, event: QInputMethodEvent):
        if self._is_text_view_mode:
            super().inputMethodEvent(event)
            return
        commit_text = event.commitString()
        if not commit_text:
            return

        pressed_char = commit_text[0]
        target_char = self._to_clean_char(pressed_char)
        inserted_image = self._insert_symbol_image(pressed_char, target_char)
        if not inserted_image:
            super().inputMethodEvent(event)
        self.update()

    def switchToTextView(self):
        if self._is_text_view_mode:
            return
        self._is_text_view_mode = True

        scroll_position = self.verticalScrollBar().value()
        cursor = self.textCursor()
        cursor_position = cursor.position()

        self.blockSignals(True)
        plain_text_accumulator = []

        block = self.document().begin()
        user_prop_char = int(QTextFormat.Property.UserProperty) + 1

        while block.isValid():
            iterator = block.begin()
            while not iterator.atEnd():
                fragment = iterator.fragment()
                if fragment.isValid():
                    char_format = fragment.charFormat()
                    if char_format.isImageFormat():
                        img_format = char_format.toImageFormat()
                        original_char = img_format.property(user_prop_char)
                        if original_char:
                            # SOLUCIÓN: Multiplicamos el carácter por la longitud del fragmento
                            # Si Qt llegó a fusionar fragmentos con el mismo formato, fragment.length()
                            # nos dirá exactamente cuántas imágenes seguidas hay en este bloque.
                            plain_text_accumulator.append(
                                str(original_char) * fragment.length()
                            )
                    else:
                        plain_text_accumulator.append(fragment.text())
                iterator += 1

            block = block.next()
            if block.isValid():
                plain_text_accumulator.append("\n")

        self.setPlainText("".join(plain_text_accumulator))

        cursor.setPosition(cursor_position)
        self.setTextCursor(cursor)

        block_format = QTextBlockFormat()
        # block_format.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # Aplicar el formato a todos los bloques del documento actual de golpe
        cursor_global = self.textCursor()
        cursor_global.select(QTextCursor.SelectionType.Document)
        cursor_global.mergeBlockFormat(block_format)

        self._applyMargin()
        self.verticalScrollBar().setValue(scroll_position)        
        self.blockSignals(False)

    def switchToImageView(self):

        if not self._is_text_view_mode:
            return
        self._is_text_view_mode = False
        scroll_position = self.verticalScrollBar().value()
        cursor = self.textCursor()
        cursor_position = cursor.position()
        self.blockSignals(True)

        current_text = self.toPlainText()
        self.clear()

        # cursor = self.textCursor()

        for char in current_text:
            if char in ("\n", "\r"):  ## Verificar
                cursor.insertBlock()
                continue

            target_char = self._to_clean_char(char)
            if not self._symbol_mapper.has_image(target_char):
                cursor.insertText(char)
            self._insert_symbol_image(char, target_char)
        cursor.setPosition(cursor_position)
        self.setTextCursor(cursor)
        self._applyMargin()
        # block_format = QTextBlockFormat()
        # block_format.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.verticalScrollBar().setValue(scroll_position)
        self.blockSignals(False)

    def _applyMargin(self):
        root_frame = self.doc.rootFrame()
        padding = self.innerPadding
        if root_frame:
            frame_format = root_frame.frameFormat()
            frame_format.setLeftMargin(self.margin + padding)
            frame_format.setRightMargin(self.margin - padding)
            frame_format.setTopMargin(self.margin)
            frame_format.setBottomMargin(self.margin)
            # frame_format.setHeight(self.page_height) # Esto hace que se cargue el alto completo de la primera página incluyendo el scrollbar si es necesario
            root_frame.setFrameFormat(frame_format)

    def paintEvent(self, event):

        doc = self.document()
        if doc.pageSize() != QSizeF(self.page_width, self.page_height):
            doc.setPageSize(QSizeF(self.page_width, self.page_height))

        painter = QPainter(self.viewport())
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        page_count = doc.pageCount()

        scroll_y = self.verticalScrollBar().value()

        viewport_width = self.viewport().width()
        x_offset = (viewport_width - self.page_width) // 2

        for i in range(page_count):
            page_top = i * (self.page_height + self.page_gap) + self.page_gap - scroll_y
            page_rect = QRectF(x_offset, page_top, self.page_width, self.page_height)

            painter.fillRect(page_rect, self._page_color)
            painter.setPen(QPen(QColor("#cccccc"), 2))  # La línea entre páginas
            painter.drawRect(page_rect)

        painter.end()

        super().paintEvent(event)


    ## Método funcionando. Queda limpiarlo.
    def change_scale(self, scale):

        self.page_height = int(self.page_height  * scale)
        self.page_width = int(self.page_width * scale)
        # self._init_font_size = 60 * scale
        viewport_width = self.viewport().width() * scale
        self.viewport().setFixedWidth(viewport_width * scale)
        self.setWordWrapMode(QTextOption.WrapMode.WrapAnywhere)
        self.setLineWrapMode(QTextEdit.LineWrapMode.FixedPixelWidth)
        self.setLineWrapColumnOrWidth(self.page_width)


        ## Monospace cross platform
        fuente_original = QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont)
        fuente_original.setPointSize(self.font().pointSize() * scale)
        fuente_original.setLetterSpacing(QFont.SpacingType.PercentageSpacing, 140)
        self.setFont(fuente_original)
        font_metrics = QFontMetrics(self.font())
        font_height = font_metrics.height()

        block_format = QTextBlockFormat()

        ### Sirve para setear la alineación del documento completo.
        ### El problema es que no logro que el pintado de las imágenes se ajuste a la alineación
        # block_format.setAlignment(Qt.AlignmentFlag.AlignCenter) #### Sirve para setear la alineación del documento completo.

        block_format.setLineHeight(float(font_height), 2)
        cursor = self.textCursor()
        cursor.setBlockFormat(block_format)
        self.setTextCursor(cursor)

        self.margin = int(self.margin * scale)
        self.innerPadding = int(self.innerPadding * scale)
        # self.doc = self.document()
        # self._applyMargin()

        # 3. Estilo Visual
        self._applyMargin()
        self.doc.setPageSize(QSize(self.page_width, self.page_height))
        self.document().setPageSize(QSize(self.page_width, self.page_height))

        self.setFixedWidth(self.page_width + self.innerPadding * 2)
        self.switchToTextView()
        self.switchToImageView()