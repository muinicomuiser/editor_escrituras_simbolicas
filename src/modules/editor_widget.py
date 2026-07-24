from PySide6.QtWidgets import QTextEdit
from PySide6.QtGui import (
    QFontMetrics,
    QKeyEvent,
    QInputMethodEvent,
    QTextBlockFormat,
    QTextCharFormat,
    QTextImageFormat,
    QTextFormat,
    QPainter,
    QPen,
    QColor,
    QTextOption,
)
from PySide6.QtCore import QRectF, Qt, QSizeF
from modules.symbol_mapper import SymbolMapper


class EditorWidget(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.m_mapper = SymbolMapper()
        self.m_imageScale = 1.0
        self.m_isTextViewMode = False

        self.page_height = 1123
        self.page_width = 794

        self.setAcceptRichText(True)
        self.setWordWrapMode(QTextOption.WrapMode.WrapAnywhere)
        self.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth) ###

        # 1. Configuración de Fuente Base
        fuente_original = self.font()

        fuente_original.setPointSize(40)
        # fuente_original.setFamily("Monospace")
        fuente_original.setFamily("DejaVu Sans Mono")
        # fuente_original.setWordSpacing(24.0)
        fuente_original.setWordSpacing(32.0)
        self.setFont(fuente_original)

        font_metrics = QFontMetrics(self.font())
        # print(font_metrics.size(Qt.TextSingleLine, " ").width())
        font_height = font_metrics.size(Qt.TextSingleLine, " ").height()

        block_format = QTextBlockFormat()
        block_format.setLineHeight(float(font_height), 2)
        cursor = self.textCursor()
        cursor.setBlockFormat(block_format)
        self.setTextCursor(cursor)        
        # block_format.setLineHeight(30, QTextBlockFormat.LineHeightTypes.FixedHeight)
        # 2. Configurar documento en formato A4 (794x1123 a 96 DPI)

        self.margin = 40
        self.doc = self.document()
        self.doc.setPageSize(QSizeF(self.page_width, self.page_height))
        # self.doc.setTextWidth(self.page_width)
        self.page_gap = 0
        self.applyMargin()
        # root_frame = self.doc.rootFrame()
        # if root_frame:
        #     frame_format = root_frame.frameFormat()
        #     frame_format.setMargin(self.margin)  # Margen interno de la página
        #     root_frame.setFrameFormat(frame_format)
            

        # 3. Estilo Visual
        self.setStyleSheet("QTextEdit { background-color: #333333; color: #444444; }")
        # self.setStyleSheet("QTextEdit { background-color: white; color: #444444; }")
        self.setFixedWidth(self.page_width + 40)
        # self.setFixedWidth(794)

    def setImageScale(self, scale: float):
        if scale > 0.1:
            self.m_imageScale = scale

    def keyPressEvent(self, event: QKeyEvent):
        # Delegar controles nativos directamente si corresponde
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
        target_char = pressed_char.lower()

        if self.m_mapper.has_image(target_char):
            image_format = QTextImageFormat()
            image_format.setName(self.m_mapper.get_image_path(target_char))
            image_format.setWidth(32 * self.m_imageScale)
            image_format.setHeight(32 * self.m_imageScale)

            # NOTA: En PySide6 se debe convertir el enum UserProperty a int para operaciones aritméticas
            user_prop_key = int(QTextFormat.Property.UserProperty) + 1
            image_format.setProperty(user_prop_key, text)

            cursor = self.textCursor()
            formato_limpio = self.currentCharFormat()
            cursor.setCharFormat(formato_limpio)

            cursor.insertImage(image_format)
            self.setTextCursor(cursor)
            return

        super().keyPressEvent(event)
        self.update()

    def switchToTextView(self):
        if self.m_isTextViewMode:
            return
        self.m_isTextViewMode = True


        cursor = self.textCursor()
        cursor_position = cursor.position()


        self.blockSignals(True)
        plain_text_accumulator = []

        # Iteración de bloques lógicos del QTextDocument
        block = self.document().begin()
        user_prop_key = int(QTextFormat.Property.UserProperty) + 1

        while block.isValid():
            iterator = block.begin()
            while not iterator.atEnd():
                fragment = iterator.fragment()
                if fragment.isValid():
                    char_format = fragment.charFormat()
                    if char_format.isImageFormat():
                        img_format = char_format.toImageFormat()
                        original_char = img_format.property(user_prop_key)
                        if original_char:
                            plain_text_accumulator.append(str(original_char))
                    else:
                        plain_text_accumulator.append(fragment.text())
                iterator += 1  # Operador de incremento mapeado en PySide6

            block = block.next()
            if block.isValid():
                plain_text_accumulator.append("\n")

        self.setPlainText("".join(plain_text_accumulator))
        self.applyMargin()

        cursor.setPosition(cursor_position)
        self.setTextCursor(cursor)

        self.blockSignals(False)
        

    def switchToImageView(self):

        if not self.m_isTextViewMode:
            return
        self.m_isTextViewMode = False
        self.blockSignals(True)

        cursor = self.textCursor()
        cursor_position = cursor.position()        

        current_text = self.toPlainText()
        self.clear()

        cursor = self.textCursor()

        # Mapa de filtrado de acentos y caracteres especiales
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
        user_prop_key = int(QTextFormat.Property.UserProperty) + 1

        for char in current_text:
            if char in ("\n", "\r"):
                cursor.insertBlock()
                continue

            target_char = tildes.get(char, char).lower()

            if self.m_mapper.has_image(target_char):
                image_path = self.m_mapper.get_image_path(target_char)
                image_format = QTextImageFormat()
                image_format.setName(image_path)

                base_size = 32
                image_format.setWidth(base_size * self.m_imageScale)
                image_format.setHeight(base_size * self.m_imageScale)
                image_format.setProperty(user_prop_key, char)

                cursor.insertImage(image_format)
            else:
                cursor.insertText(char)

        self.applyMargin()

        cursor.setPosition(cursor_position)
        self.setTextCursor(cursor)

        self.blockSignals(False)

    def inputMethodEvent(self, event: QInputMethodEvent):
        if self.m_isTextViewMode:
            super().inputMethodEvent(event)
            return

        commit_text = event.commitString()
        if commit_text:
            pressed_char = commit_text[0]

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
            target_char = tildes.get(pressed_char, pressed_char).lower()

            if self.m_mapper.has_image(target_char):
                image_format = QTextImageFormat()
                image_format.setName(self.m_mapper.get_image_path(target_char))
                image_format.setWidth(32 * self.m_imageScale)
                image_format.setHeight(32 * self.m_imageScale)
                image_format.setVerticalAlignment(QTextCharFormat.VerticalAlignment.AlignMiddle)

                user_prop_key = int(QTextFormat.Property.UserProperty) + 1
                image_format.setProperty(user_prop_key, commit_text)

                cursor = self.textCursor()
                formato_limpio = self.currentCharFormat()
                cursor.setCharFormat(formato_limpio)
                cursor.insertImage(image_format)
                self.setTextCursor(cursor)

                event.accept()
                return

        super().inputMethodEvent(event)
        self.update()

    def changeAssetsDirectory(self, path: str):
        self.m_mapper.load_from_directory(path)

        if not self.m_isTextViewMode and not self.document().isEmpty():
            self.switchToTextView()
            self.switchToImageView()

    def getAssetsDirectory(self) -> str:
        return self.m_mapper.get_current_directory()

    # def paintEvent(self, event):
    #     super().paintEvent(event)

    #     painter = QPainter(self.viewport())
    #     painter.setPen(QPen(QColor("#555555"), 2, Qt.PenStyle.DashLine))

    #     page_height = int(self.document().pageSize().height())
    #     if page_height <= 0:
    #         page_height = 1123

    #     total_height = int(self.document().size().height())
    #     scroll_y = self.verticalScrollBar().value()

    #     # Dibujado dinámico de líneas discontinuas en los quiebres de página físicos
    #     for y in range(page_height, total_height, page_height):
    #         visual_y = y - scroll_y
    #         if 0 <= visual_y <= self.viewport().height():
    #             painter.drawLine(0, visual_y, self.viewport().width(), visual_y)

    def applyMargin(self):
        root_frame = self.doc.rootFrame()
        if root_frame:
            frame_format = root_frame.frameFormat()
            # frame_format.setMargin(margin)  # Margen interno de la página
            frame_format.setLeftMargin(self.margin)
            frame_format.setRightMargin(self.margin)
            frame_format.setTopMargin(self.margin)
            frame_format.setBottomMargin(self.margin)            

            root_frame.setFrameFormat(frame_format)

    def paintEvent(self, event):

        doc = self.document()
        if doc.pageSize() != QSizeF(self.page_width, self.page_height):
            doc.setPageSize(QSizeF(self.page_width, self.page_height))    

        # self.applyMargin()
        # layout = doc.documentLayout()
        # if layout:
        #     # Esto obliga a Qt a dividir los bloques en páginas físicas
        #     layout.p(QSizeF(self.page_width, self.page_height))                
        # """Sobrescribimos el evento de pintado para dibujar las hojas de papel."""
        painter = QPainter(self.viewport())
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        doc = self.document()
        page_count = doc.pageCount()

        # Posición del scroll actual
        scroll_y = self.verticalScrollBar().value()
        
        # Centrar la hoja horizontalmente en el viewport
        viewport_width = self.viewport().width()
        x_offset = max(20, (viewport_width - self.page_width) // 2)

        # 3. Dibujar cada hoja de papel antes de renderizar el texto
        for i in range(page_count):
            page_top = i * (self.page_height + self.page_gap) + self.page_gap - scroll_y
            page_rect = QRectF(x_offset, page_top, self.page_width, self.page_height)

            # Dibujar sombra ligera detrás de la página
            # shadow_rect = page_rect.translated(3, 3)
            # painter.fillRect(shadow_rect, QColor("#b0b0b0"))

            # Dibujar la hoja de papel blanca
            painter.fillRect(page_rect, Qt.GlobalColor.white)
            # print(f"{i}: {page_top}")
            painter.setPen(QPen(QColor("#cccccc"), 2))
            painter.drawRect(page_rect)

        painter.end()

        # 4. Dejar que QTextEdit pinte el texto y el cursor nativo por encima
        super().paintEvent(event)