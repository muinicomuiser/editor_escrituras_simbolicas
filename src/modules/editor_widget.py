from PySide6.QtWidgets import QTextEdit
from PySide6.QtGui import (
    QKeyEvent,
    QInputMethodEvent,
    QTextImageFormat,
    QTextFormat,
    QPainter,
    QPen,
    QColor,
)
from PySide6.QtCore import Qt, QSizeF
from modules.symbol_mapper import SymbolMapper


class EditorWidget(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.m_mapper = SymbolMapper()
        self.m_imageScale = 1.0
        self.m_isTextViewMode = False

        self.setAcceptRichText(True)

        # 1. Configuración de Fuente Base
        fuente_original = self.font()
        fuente_original.setPointSize(24)
        fuente_original.setFamily("Monospace")
        fuente_original.setWordSpacing(32.0)
        self.setFont(fuente_original)

        # 2. Configurar documento en formato A4 (794x1123 a 96 DPI)
        doc = self.document()
        doc.setPageSize(QSizeF(794, 1123))

        root_frame = doc.rootFrame()
        if root_frame:
            frame_format = root_frame.frameFormat()
            frame_format.setMargin(40)  # Margen interno de la página
            root_frame.setFrameFormat(frame_format)

        # 3. Estilo Visual
        self.setStyleSheet("QTextEdit { background-color: white; color: #444444; }")
        self.setFixedWidth(834)

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
            return  # Consumimos el evento

        super().keyPressEvent(event)
        self.update()

    def switchToTextView(self):
        if self.m_isTextViewMode:
            return
        self.m_isTextViewMode = True

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
        self.blockSignals(False)

    def switchToImageView(self):
        if not self.m_isTextViewMode:
            return
        self.m_isTextViewMode = False

        current_text = self.toPlainText()
        self.clear()

        cursor = self.textCursor()
        self.blockSignals(True)

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

    def paintEvent(self, event):
        super().paintEvent(event)

        painter = QPainter(self.viewport())
        painter.setPen(QPen(QColor("#555555"), 2, Qt.PenStyle.DashLine))

        page_height = int(self.document().pageSize().height())
        if page_height <= 0:
            page_height = 1123

        total_height = int(self.document().size().height())
        scroll_y = self.verticalScrollBar().value()

        # Dibujado dinámico de líneas discontinuas en los quiebres de página físicos
        for y in range(page_height, total_height, page_height):
            visual_y = y - scroll_y
            if 0 <= visual_y <= self.viewport().height():
                painter.drawLine(0, visual_y, self.viewport().width(), visual_y)
