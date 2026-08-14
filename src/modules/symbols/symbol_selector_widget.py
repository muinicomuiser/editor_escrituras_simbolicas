import copy
from pathlib import Path
from itertools import chain
from PySide6.QtCore import QSize, Signal
from PySide6.QtGui import QAction, QPixmap
from PySide6.QtWidgets import QComboBox, QGridLayout, QLabel, QMainWindow, QScrollArea, QSizePolicy, QToolBar, QVBoxLayout, QWidget
from modules.symbols.symbol_drop_surface import SymbolDropSurface
from modules.persistence.symbols_collections_file_manager import SymbolsCollectionFileManager
from modules.symbols.symbol_mapper import SymbolMapper

class SymbolSelectorWindow(QMainWindow):
    symbols_changed = Signal()    
    def __init__(self, symbol_mapper: SymbolMapper, parent=None):
        super().__init__(parent)
        self._symbol_mapper = symbol_mapper

        # Propiedades base
        self._drop_container_object_name = "SymbolDropContainer"
        self._drop_container_surface_object_name = "SymbolDropSurface"

        self._columns_count = 4
        self._base_size = QSize(720, 560)
        self._drop_surface_size = QSize(160, 220)

        self.characters = {
            "single": list("abcdefghijklmnñopqrstuvwxyz"),
            "compound": ["ch", "ll"]
        }
        self._collections = []
        self._current_collection = {}
        # self._current_symbols = {} # Ya tengo esta información en cada drop_surface
        self._drop_surfaces: dict[str, SymbolDropSurface] = {}

        # Contenedores principales
        self._container = QWidget()
        self._main_layout = QGridLayout(self._container)
        self._scroll_area = QScrollArea()
        self._scroll_area.setWidgetResizable(True)
        self._scroll_area.setWidget(self._container)
        self.setCentralWidget(self._scroll_area)

        # Persistencia
        self._collection_file_manager = SymbolsCollectionFileManager()

        # Setup de componentes
        self._load_collections_list()
        self._setup_toolbar()
        self._setup_drop_containers()

        # style                
        self.setWindowTitle("Editor de colección de símbolos")
        self.resize(self._base_size)
        self.setMinimumSize(self._base_size)
        self.setStyleSheet("""
            #SymbolDropContainer {
                border: 1px solid #888888;
            }
            #SymbolDropSurface {
                background-color: #ffffff;
            }
        """)
    
    def closeEvent(self, event):
        # self.deleteLater() # Tiene más sentido que no se destruya el editor
        for value in self.characters.values():
            for char in value:
                self._drop_surfaces[char].pixmap = self._symbol_mapper.get_pixmap(char)
        event.accept()    

    def _set_symbol(self, char, image_path, is_saved): # Trabajando acá
        # self._current_symbols[char] = image_path # Ya tengo esta información en cada drop surface
        if not is_saved:
            self._collection_file_manager.set_to_unsaved()
    def _on_collection_selected(self, index: int):
        if index < 0:
            return
        selected_collection = self.saved_symbols_list_box.itemData(index)

        if selected_collection is not None:
            self._current_collection = selected_collection
            dir_path = Path(selected_collection.directory)
            for path in dir_path.iterdir():
                char_image_path = path.absolute()
                char = path.name.replace(path.suffix, "")
                drop_surface = self._drop_surfaces.get(char, None)
                if drop_surface:
                    drop_surface.set_image(char_image_path, is_saved=True)
            self._set_collection_symbols()        
            self.symbols_changed.emit()
        else:
            # Caso donde seleccionan el placeholder ("Selecciona una colección...")
            print("Ninguna colección seleccionada")

    def _on_collection_saved(self):
        self._set_collection_symbols()
        self._collection_file_manager.set_to_saved()
        self.symbols_changed.emit()

    def _set_collection_symbols(self):
        """Limpia los pixmap del Symbol Maper y le asigna los pixmap de cada Drop Surface """
        self._symbol_mapper.clear_map()
        for char, surface in self._drop_surfaces.items():
            self._symbol_mapper.set_pixmap(char, surface.pixmap)
            # self._symbol_mapper.set_pixmap(char, copy(surface.pixmap))


    def _load_collections_list(self):
        collections_file = self._collection_file_manager.openFile(self._collection_file_manager.collections_persistence_file)
        self._collections = collections_file.collections

    def _setup_toolbar(self):
        toolbar = QToolBar("Barra de Herramientas Symbols", self)
        self.addToolBar(toolbar)

        self._save_colection_action = QAction("Guardar", self)
        self._save_colection_action.triggered.connect(self._on_collection_saved)

        saved_symbols_list_label = QLabel("Colecciones guardadas", self)
        self.saved_symbols_list_box = QComboBox(self)

        self.saved_symbols_list_box.setPlaceholderText("Selecciona una colección...")
        self.saved_symbols_list_box.setCurrentIndex(-1) 
        self.saved_symbols_list_box.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        self.saved_symbols_list_box.setMinimumContentsLength(15) 
        self.saved_symbols_list_box.setMaximumWidth(200)
        self.saved_symbols_list_box.setSizePolicy(
            QSizePolicy.Policy.MinimumExpanding, 
            QSizePolicy.Policy.Fixed      
        )        
        for collection in self._collections:
            self.saved_symbols_list_box.addItem(collection.collection_name, collection)

        self.saved_symbols_list_box.currentIndexChanged.connect(self._on_collection_selected)
        spacer_left = QWidget()
        spacer_left.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        toolbar.addWidget(spacer_left)
        toolbar.addWidget(saved_symbols_list_label)
        toolbar.addWidget(self.saved_symbols_list_box)
        toolbar.addSeparator()
        toolbar.addAction(self._save_colection_action)
        spacer_right = QWidget()
        spacer_right.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        toolbar.addWidget(spacer_right)

    def _setup_drop_containers(self):
        for idx, character in enumerate(chain.from_iterable(self.characters.values())):
            drop_container = QWidget()
            drop_layout = QVBoxLayout(drop_container)
            drop_surface = SymbolDropSurface(symbol_name=character)
            drop_label = QLabel(character)
            drop_label.setMaximumHeight(drop_label.fontMetrics().height())
            drop_layout.addWidget(drop_label)
            drop_layout.addWidget(drop_surface)
            drop_container.setFixedSize(self._drop_surface_size)

            drop_container.setObjectName(self._drop_container_object_name)
            drop_surface.setObjectName(self._drop_container_surface_object_name)
            drop_surface.image_dropped.connect(lambda image_path, from_saved, char=character: self._set_symbol(char, image_path, from_saved))

            row, col = idx // self._columns_count, idx % self._columns_count
            self._main_layout.addWidget(drop_container, row, col)

            self._drop_surfaces[character] = drop_surface
