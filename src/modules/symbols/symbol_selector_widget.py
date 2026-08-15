from pathlib import Path
from itertools import chain
import sys
from PySide6.QtCore import QSize, Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QComboBox, QGridLayout, QInputDialog, QLabel, QMainWindow, QMessageBox, QPushButton, QScrollArea, QSizePolicy, QToolBar, QVBoxLayout, QWidget
from modules.symbols.symbol_drop_surface import SymbolDropSurface
from modules.persistence.symbols_collections_file_manager import SymbolsCollectionFileManager
from modules.symbols.symbol_mapper import SymbolMapper
from modules.shared.models.symbol_collection_model import SymbolCollectionModel

class SymbolSelectorWindow(QMainWindow):
    symbols_changed = Signal()    
    def __init__(self, symbol_mapper: SymbolMapper, parent=None):
        super().__init__(parent)
        self._symbol_mapper = symbol_mapper

        # Propiedades base
        self._drop_container_object_name = "SymbolDropContainer"
        self._drop_container_surface_object_name = "SymbolDropSurface"

        self._columns_count = 4
        self._base_size = QSize(920, 560)
        self._drop_surface_size = QSize(160, 220)

        self.characters = {
            "single": list("abcdefghijklmnñopqrstuvwxyz"),
            "compound": ["ch", "ll"]
        }
        self._collections = []
        self._current_collection = {}
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
        self._collections_persistence_dir = Path(getattr(sys, '_MEIPASS', Path(".").absolute()), "data/simbolos")
        self.collections_persistence_file = self._collections_persistence_dir.joinpath("symbol_collections.json")
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
        for value in self.characters.values():
            for char in value:
                self._drop_surfaces[char].pixmap = self._symbol_mapper.get_pixmap(char)
        # self.deleteLater() # Pensar si es necesario destruir el editor, si los pixmaps los conserva el mapper
        event.accept()    

    def _set_symbol(self, char, image_path, is_saved): # Trabajando acá
        if not is_saved:
            self._collection_file_manager.set_to_unsaved()
    def _on_collection_selected(self, index: int):
        if index < 0:
            return
        selected_collection: SymbolCollectionModel = self.saved_symbols_list_box.itemData(index)

        if selected_collection is not None:
            self._clear_surfaces()
            self._current_collection = selected_collection
            # dir_path = Path(selected_collection.directory)
            dir_path = self._collection_file_manager.get_collections_persistence_dir().joinpath(selected_collection.directory)
            for path in dir_path.iterdir():
                char_image_path = path.absolute()
                char = path.name.replace(path.suffix, "")
                drop_surface = self._drop_surfaces.get(char, None)
                if drop_surface:
                    drop_surface.set_image(char_image_path, is_saved=True)
            self._set_collection_symbols()  
            self._collection_file_manager.set_to_saved()                  
            self.symbols_changed.emit()
        else:
            # Caso donde seleccionan el placeholder ("Selecciona una colección...")
            print("Ninguna colección seleccionada")

    def _clear_surfaces(self):
        if not self._collection_file_manager.is_saved():
            pass ## POR TRABAJAR

        self._current_collection = {}
        for surface in self._drop_surfaces.values():
            surface.clear()


    def _on_create_collection(self):
        self._clear_surfaces()
        self.saved_symbols_list_box.setCurrentIndex(-1)
        # self.symbols_changed.emit()

    def _on_save_collection(self):
        if not self._current_collection:
            self._on_save_collection_as()
        elif self._collection_file_manager.is_saved():
            pass
        else:
            button = QMessageBox.question(self, "Guardar cambios", "¿Confirmas que quieres guardar los cambios?", buttons=QMessageBox.StandardButton.No | QMessageBox.StandardButton.Yes)
            if button == QMessageBox.StandardButton.Yes:
            # button = QMessageBox.question(self, "¿Confirmas que quieres guardar los cambios?", buttons=QMessageBox.StandardButton.No | QMessageBox.StandardButton.Yes) == QMessageBox.StandardButton.Yes:
            # if button == QMessageBox.StandardButton.Yes:
                collection_dir = self._collection_file_manager._collections_persistence_dir.joinpath(self._current_collection.directory)
                if not collection_dir.is_dir():
                    collection_dir.mkdir(parents=True, exist_ok=True)
                files = {item.name.split(".")[0]: item.name for item in collection_dir.iterdir()}
                for surface in self._drop_surfaces.values():
                    filename = files.get(surface.symbol_name, None)
                    if not surface.has_symbol() and filename:
                        Path(collection_dir.joinpath(filename)).unlink(missing_ok=True)
                    surface.save_to_file(collection_dir)
                self._on_collection_selected(self.saved_symbols_list_box.currentIndex())
                # self.saved_symbols_list_box.setCurrentIndex(self.saved_symbols_list_box.currentIndex())    


    def _on_save_collection_as(self):

        ## Esta lógica debería ir en symbol file manager, que funciona como repository
        ## El find, find one, add collection
        get_name_widget = QWidget(self)

        new_name, ok = QInputDialog.getText(get_name_widget, "Nombre de la colección", "Ponle un nombre a tu colección:")   

        if not ok:
            return

        # new_name = "Nueva colección"
        saved_collection = self._collection_file_manager.find_by_name(new_name)
        if saved_collection:
            ## Error
            print("La colección ya existe, deseas sobreescribirla")            
            return

        ## Acá modifico el nombre de la colección para asignar el nombre de directorio
        new_dir = new_name.strip().replace(" ", "_")
        new_collection = SymbolCollectionModel(
            collection_name=new_name,
            directory=new_dir
        )
        collection_dir = self._collection_file_manager._collections_persistence_dir.joinpath(new_dir)
        if not collection_dir.is_dir():
            collection_dir.mkdir(parents=True, exist_ok=True)
        for surface in self._drop_surfaces.values():
            surface.save_to_file(collection_dir)

        self._collection_file_manager.add_collection(new_collection)
        self.saved_symbols_list_box.addItem(new_collection.collection_name, new_collection)

        # Esta acción está emitiendo la señal para actualizar los símbolos y setear el filemanager como saved
        self.saved_symbols_list_box.setCurrentIndex(self.saved_symbols_list_box.count() - 1)         

    def _set_collection_symbols(self):
        """Limpia los pixmap del Symbol Maper y le asigna los pixmap de cada Drop Surface"""
        self._symbol_mapper.clear_map()
        for char, surface in self._drop_surfaces.items():
            self._symbol_mapper.set_pixmap(char, surface.pixmap)


    def _load_collections_list(self):
        collections_file = self._collection_file_manager.openFile()
        self._collections = collections_file.collections

    def _setup_toolbar(self):
        toolbar = QToolBar("Barra de Herramientas Symbols", self)
        self.addToolBar(toolbar)

        self._create_collection_action = QAction("Crear", self)
        self._create_collection_action.triggered.connect(self._on_create_collection)

        self._save_collection_action = QAction("Guardar cambios", self)
        self._save_collection_action.triggered.connect(self._on_save_collection)

        self._save_collection_as_action = QAction("Guardar como nueva colección", self)
        self._save_collection_as_action.triggered.connect(self._on_save_collection_as)

        self._rename_collection_action = QAction("Renombrar", self)
        self._rename_collection_action.triggered.connect(lambda: print("Por construir"))

        self._delete_collection_action = QAction("Eliminar", self)
        self._delete_collection_action.triggered.connect(lambda: print("Por construir"))

        saved_symbols_list_label = QLabel("Colecciones", self)
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
        toolbar.addAction(self._create_collection_action)
        toolbar.addAction(self._rename_collection_action)
        toolbar.addAction(self._save_collection_action)
        toolbar.addAction(self._save_collection_as_action)
        toolbar.addAction(self._delete_collection_action)
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

            drop_clear_button = QPushButton("Remover")
            drop_clear_button.clicked.connect(drop_surface.clear)
            drop_clear_button.clicked.connect(self._collection_file_manager.set_to_unsaved)
            drop_layout.addWidget(drop_clear_button)

            drop_container.setFixedSize(self._drop_surface_size)

            drop_container.setObjectName(self._drop_container_object_name)
            drop_surface.setObjectName(self._drop_container_surface_object_name)
            drop_surface.image_dropped.connect(lambda image_path, from_saved, char=character: self._set_symbol(char, image_path, from_saved))

            row, col = idx // self._columns_count, idx % self._columns_count
            self._main_layout.addWidget(drop_container, row, col)

            self._drop_surfaces[character] = drop_surface
