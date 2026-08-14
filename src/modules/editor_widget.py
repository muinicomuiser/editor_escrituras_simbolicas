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
from PySide6.QtCore import QRectF, QUrl, Qt, QSizeF
from modules.config.config import Config
from modules.symbols.symbol_mapper import SymbolMapper


class EditorWidget(QTextEdit):
    def __init__(self, config: Config, symbol_mapper: SymbolMapper, parent=None):
        super().__init__(parent)
        self.config = config

        self._symbol_mapper = symbol_mapper

        self.page_height = self.config.HEIGHT
        self.page_width = self.config.WIDTH

        self.m_imageScale = 1.0
        self._init_font_size = 40

        self.m_isTextViewMode = False

        self.setAcceptRichText(True)
        self.setWordWrapMode(QTextOption.WrapMode.WrapAnywhere)
        self.setLineWrapMode(QTextEdit.LineWrapMode.FixedPixelWidth)
        self.setLineWrapColumnOrWidth(self.page_width)


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
        self.setStyleSheet(f"QTextEdit {{ background-color: {self._background_color}; color: {self._font_color}; }}")
        self.setFixedWidth(self.page_width + self.innerPadding * 2)
        # self.setFixedWidth(794)



    def setImageScale(self, scale: float):
        if scale > 0.1:
            self.m_imageScale = scale

    def setFontSize(self, fontSize: int):
        fuente = self.font()
        fuente.setPointSize(fontSize)
        fuente.setWordSpacing(float(fontSize))
        self.setFont(fuente)
        font_metrics = QFontMetrics(self.font())
        font_width = font_metrics.horizontalAdvance("W")
        nueva_escala = float(font_width) / 24.0
        self.setImageScale(nueva_escala)

    # Método creado, por revisar
    def setContent(self, plain_text_content: str):
        self.clear()
        self.setPlainText(plain_text_content)

    def setAssetsDirectory(self, path: str): ## Revisar
    
        self._symbol_mapper.load_from_directory(path)

        if not self.m_isTextViewMode and not self.document().isEmpty():
            self.switchToTextView()
            self.switchToImageView()

    def getAssetsDirectory(self) -> str:
        return self._symbol_mapper.get_current_directory()

    def _to_clean_char(self, char: str):
        tildes = {
            "á": "a",
            "Á": "a",
            "é": "e",
            "É": "e",
            "í": "i",
            "Í": "i",
            "ó": "o",
            "Ó": "o",
            "ú": "u",
            "Ú": "u",
            "ü": "u",
            "Ü": "u",
            "ñ": "ñ",
            "Ñ": "ñ",
        }        
        return tildes.get(char, char).lower()

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
                Qt.TransformationMode.SmoothTransformation
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
            doc.addResource(QTextDocument.ResourceType.ImageResource, resource_url, canvas.toImage())

        image_format = QTextImageFormat()
        image_format.setName(resource_url.toString())
        image_format.setWidth(char_width)
        image_format.setHeight(char_height)
        image_format.setVerticalAlignment(QTextCharFormat.VerticalAlignment.AlignBaseline)

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
        if self.m_isTextViewMode or event.key() in (
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
        if self.m_isTextViewMode:
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
        # super().inputMethodEvent(event)
        # self.update()






    def switchToTextView(self):
        if self.m_isTextViewMode:
            return
        self.m_isTextViewMode = True

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
        self.blockSignals(False)


    def switchToImageView(self):

        if not self.m_isTextViewMode:
            return
        self.m_isTextViewMode = False
        self.blockSignals(True)

        cursor = self.textCursor()
        # cursor_position = cursor.position()

        current_text = self.toPlainText()
        self.clear()

        cursor = self.textCursor()

        for char in current_text:
            if char in ("\n", "\r"): ## Verificar
                cursor.insertBlock()
                continue

            target_char = self._to_clean_char(char)
            if not self._symbol_mapper.has_image(target_char):
                cursor.insertText(char)
            self._insert_symbol_image(char, target_char)

        self._applyMargin()
        # block_format = QTextBlockFormat()
        # block_format.setAlignment(Qt.AlignmentFlag.AlignCenter)        
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

            painter.fillRect(page_rect, Qt.GlobalColor.white)
            painter.setPen(QPen(QColor("#cccccc"), 2))
            painter.drawRect(page_rect)

        painter.end()

        super().paintEvent(event)


    # RESPALDO

    # def _insert_image(self, pressed_char: str, target_char: str):
    ## Requiere definir una escala, o manejar dinámicamente la escala de las imágenes

    #     if not self._symbol_mapper.has_image(target_char):
    #         return False
    #     image_format = QTextImageFormat()
    #     image_format.setName(self._symbol_mapper.get_image_path(target_char))
    #     image_format.setWidth(32 * self.m_imageScale)
    #     image_format.setHeight(32 * self.m_imageScale)
    #     image_format.setVerticalAlignment(
    #         QTextCharFormat.VerticalAlignment.AlignMiddle
    #     )
    #     user_prop_char = int(QTextFormat.Property.UserProperty) + 1
    #     user_prop_id = int(QTextFormat.Property.UserProperty) + 2

    #     image_format.setProperty(user_prop_char, pressed_char)
    #     image_format.setProperty(user_prop_id, self.m_image_counter)
    #     self.m_image_counter += 1
    #     cursor = self.textCursor()
    #     formato_actual = self.currentCharFormat()
    #     formato_actual.setFont(self.font())
    #     cursor.setCharFormat(formato_actual)
    #     cursor.insertImage(image_format)
    #     self.setTextCursor(cursor)
    #     return True

    # def switchToTextView(self):
    #     if self.m_isTextViewMode:
    #         return
    #     self.m_isTextViewMode = True

    #     cursor = self.textCursor()
    #     cursor_position = cursor.position()

    #     self.blockSignals(True)
    #     plain_text_accumulator = []

    #     block = self.document().begin()
    #     user_prop_key = int(QTextFormat.Property.UserProperty) + 1

    #     while block.isValid():
    #         iterator = block.begin()
    #         while not iterator.atEnd():
    #             fragment = iterator.fragment()
    #             if fragment.isValid():
    #                 char_format = fragment.charFormat()
    #                 if char_format.isImageFormat():
    #                     img_format = char_format.toImageFormat()
    #                     original_char = img_format.property(user_prop_key)
    #                     if original_char:
    #                         plain_text_accumulator.append(str(original_char))
    #                 else:
    #                     plain_text_accumulator.append(fragment.text())
    #             iterator += 1

    #         block = block.next()
    #         if block.isValid():
    #             plain_text_accumulator.append("\n")

    #     self.setPlainText("".join(plain_text_accumulator))
    #     self._applyMargin()

    #     # cursor.setPosition(cursor_position)
    #     # self.setTextCursor(cursor)

    #     self.blockSignals(False)