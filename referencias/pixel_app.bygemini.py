import sys
import random
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLineEdit, QPushButton, QLabel
from PySide6.QtCore import Qt, QPoint, QTimer
from PySide6.QtGui import QTextCursor

class PixelChatWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # 1. Configuración de ventana flotante sin bordes
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(400, 500)
        
        # Para arrastrar la ventana
        self.old_pos = None

        # 2. Estilo CSS global (Estilo Pixel Art Retro)
        # Se corrigió el selector del marco principal quitando el espacio intermedio (QWidget#MainFrame)
        self.setStyleSheet("""
            QWidget#MainFrame {
                background-color: #1a1a24;
                border: 4px solid #3d3d52;
                border-radius: 0px;
            }
            QLabel#TitleBar {
                background-color: #2c2c3e;
                color: #ffcc00;
                font-family: 'Courier New', monospace;
                font-weight: bold;
                font-size: 14px;
                padding: 5px;
            }
            QTextEdit {
                background-color: #0f0f14;
                color: #00ffcc;
                font-family: 'Courier New', monospace;
                font-size: 13px;
                border: 2px solid #3d3d52;
                padding: 8px;
            }
            QLineEdit {
                background-color: #0f0f14;
                color: #ffffff;
                font-family: 'Courier New', monospace;
                font-size: 13px;
                border: 2px solid #3d3d52;
                padding: 5px;
            }
            #SendButton {
                background-color: #ff0055;
                color: white;
                font-family: 'Courier New', monospace;
                font-weight: bold;
                font-size: 12px;
                border: 2px solid #3d3d52;
                padding: 5px 10px;
            }
            #SendButton:hover {
                background-color: #ff3377;
            }
            #SendButton:pressed {
                background-color: #cc0044;
                padding-top: 7px;
            }
            #Close {
                background-color: #ff0055;
                color: white;
                font-family: 'Courier New', monospace;
                font-weight: bold;
                font-size: 12px;
                border: 2px solid #3d3d52;
                padding: 2px 10px;
                height: 20px;
            }
            #Close:hover {
                background-color: #ff3377;
            }
            #Close:pressed {
                background-color: #cc0044;
            }
        """)

        # 3. Construcción de la Interfaz
        main_widget = QWidget()
        main_widget.setObjectName("MainFrame")
        self.setCentralWidget(main_widget)
        
        layout = QVBoxLayout(main_widget)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # --- NUEVA ESTRUCTURA: Barra de título superior horizontal ---
        header_container = QWidget()
        header_container.setStyleSheet("background-color: #2c2c3e; border-bottom: 4px solid #3d3d52;")
        header_layout = QHBoxLayout(header_container)
        header_layout.setContentsMargins(5, 0, 5, 0)
        header_layout.setSpacing(0)

        # Etiqueta del título
        self.title_bar = QLabel(" PIXEL_LLM_CHAT v1.0 [ESC: salir]")
        self.title_bar.setObjectName("TitleBar")
        header_layout.addWidget(self.title_bar, stretch=1) # El título se estira ocupando todo el fondo

        # Botón de cerrar incrustado a la derecha
        self.close_button = QPushButton("X")
        self.close_button.setObjectName("Close")
        self.close_button.clicked.connect(self.close)
        header_layout.addWidget(self.close_button)

        layout.addWidget(header_container)
        # -------------------------------------------------------------

        # Historial de Chat
        self.chat_history = QTextEdit()
        self.chat_history.setReadOnly(True)

        self.chat_history.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.chat_history.append("*** CONEXIÓN ESTABLECIDA CON LA IA ***\n")
        # self.chat_history.append(texto_centrado)
        layout.addWidget(self.chat_history)
        self.chat_history.setAlignment(Qt.AlignmentFlag.AlignLeft)

        # Zona inferior de entrada (Input + Botón)
        input_layout = QHBoxLayout()
        input_layout.setSpacing(6)

        self.user_input = QLineEdit()
        self.user_input.setPlaceholderText("Escribe un mensaje...")
        self.user_input.returnPressed.connect(self.send_message)
        input_layout.addWidget(self.user_input)

        self.send_button = QPushButton("ENVIAR")
        self.send_button.setObjectName("SendButton")
        self.send_button.clicked.connect(self.send_message)
        input_layout.addWidget(self.send_button)

        layout.addLayout(input_layout)

        # Respuestas simuladas del LLM
        self.dummy_responses = [
            "BEEP BOOP... Procesando tus datos humanos.",
            "Interesante pregunta. En mi simulación de 8-bits, la respuesta es 42.",
            "ERROR 404: Sentimientos no encontrados. Intenta de nuevo.",
            "¡Saludos, jugador! Estoy listo para responder.",
            "Sincronizando flujos de píxeles... Todo en orden."
        ]

    # --- Lógica de Chat ---
    def send_message(self):
        text = self.user_input.text().strip()
        if not text:
            return

        self.chat_history.append(f"[TÚ]: {text}")
        self.user_input.clear()

        self.chat_history.append("\n[IA]: ...")
        QTimer.singleShot(1000, self.simulate_ai_response)

    def simulate_ai_response(self):
        cursor = self.chat_history.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.select(QTextCursor.SelectionType.BlockUnderCursor)
        cursor.removeSelectedText()
        
        response = random.choice(self.dummy_responses)
        self.chat_history.append(f"[IA]: {response}\n")

    # --- Lógica corregida para arrastrar la ventana usando la barra de título ---
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            # Averiguamos exactamente qué widget recibió el clic
            clicked_widget = self.childAt(event.position().toPoint())
            
            # Si el clic fue en las letras del título o en el fondo de la barra de título
            if clicked_widget in [self.title_bar, self.title_bar.parentWidget()]:
                # Delegamos el movimiento nativo al sistema operativo
                self.windowHandle().startSystemMove()
                event.accept()

    # def mouseMoveEvent(self, event):
    #     if self.old_pos is not None:
    #         # Calculamos la distancia que se movió el cursor
    #         delta = event.globalPosition().toPoint() - self.old_pos
    #         # Movemos la ventana sumando esa distancia a su posición actual
    #         self.move(self.pos() + delta)
    #         # Actualizamos la posición antigua para el siguiente cuadro de movimiento
    #         self.old_pos = event.globalPosition().toPoint()
    #         event.accept()

    # def mouseReleaseEvent(self, event):
    #     if event.button() == Qt.LeftButton:
    #         self.old_pos = None

    # --- Cerrar con Escape ---
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PixelChatWindow()
    window.show()
    sys.exit(app.exec())
