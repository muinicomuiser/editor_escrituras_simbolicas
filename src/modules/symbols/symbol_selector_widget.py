from datetime import datetime
from pathlib import Path
from itertools import chain
import re
import sys
import unicodedata
from PySide6.QtCore import QBuffer, QByteArray, QIODevice, QSize, Signal, Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QComboBox,
    QGridLayout,
    QInputDialog,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QToolBar,
    QVBoxLayout,
    QWidget,
)
from modules.symbols.symbol_drop_surface import SymbolDropSurface
from modules.persistence.symbols_collections_repository import (
    SymbolsCollectionRepository,
)
from modules.symbols.symbol_mapper import SymbolMapper
from modules.shared.models.symbol_collection_model import SymbolCollectionModel
from modules.utils.logger import get_logger
from modules.persistence.file_service import FilesService
from modules.exceptions.exceptions import StorageError, DirectoryRemovalError

class SymbolSelectorWindow(QMainWindow):
    symbols_changed = Signal()

    def __init__(self, symbol_mapper: SymbolMapper, file_service: FilesService = FilesService(), parent=None):
        super().__init__(parent)     
        self._symbol_mapper = symbol_mapper

        # Propiedades base
        self.setObjectName("SymbolSelectorWindow")
        self._drop_container_object_name = "SymbolDropContainer"
        self._drop_container_surface_object_name = "SymbolDropSurface"

        self._columns_count = 4
        self._base_size = QSize(920, 560)
        self._drop_surface_size = QSize(160, 220)

        self.characters = {
            "single": list("abcdefghijklmnñopqrstuvwxyz"),
            "compound": ["ch", "ll"],
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
        self._collections_repository = SymbolsCollectionRepository()
        self._collections_persistence_dir = Path(
            getattr(sys, "_MEIPASS", Path(".").absolute()), "data/simbolos"
        )
        self.collections_persistence_file = self._collections_persistence_dir.joinpath(
            "symbol_collections.json"
        )

        self._file_service = file_service
        # Setup de componentes
        self._load_collections_list()
        self._setup_toolbar()
        self._setup_drop_containers()

        # style
        self.setWindowTitle("Editor de colección de símbolos")
        self.resize(self._base_size)
        self.setMinimumSize(self._base_size)

        self.logger = get_logger(self.__class__.__name__)
        self.logger.info(f"Módulo Iniciado")           


    def get_current_collection_name(self):
        return (
            self._current_collection.collection_name if self._current_collection else ""
        )

    def closeEvent(self, event):
        if not self.is_empty() and not self._collections_repository.is_saved():
            button = self._unsaved_changes_messagebox()
            if button == QMessageBox.StandardButton.Cancel:
                return
            elif button == QMessageBox.StandardButton.Yes:
                self._save_collection()
                for value in self.characters.values():
                    for char in value:
                        self._drop_surfaces[char].pixmap = self._symbol_mapper.get_pixmap(char)
                self._on_collection_selected(self.saved_symbols_list_box.currentIndex())
            elif button == QMessageBox.StandardButton.No:
                self._clear_surfaces()
                for value in self.characters.values():
                    for char in value:
                        self._drop_surfaces[char].pixmap = self._symbol_mapper.get_pixmap(char)
                self._collections_repository.set_to_saved()
        event.accept()

    ### Acá también hay que revisar lo que pasa si el directorio de la colección no existe.
    def _on_collection_selected(self, index: int):
        if index < 0:
            return

        if not self._collections_repository.is_saved():
            button = self._unsaved_changes_messagebox()
            if button == QMessageBox.StandardButton.Cancel:
                return
            elif button == QMessageBox.StandardButton.Yes:
                self._on_save_collection()
            elif button == QMessageBox.StandardButton.No:
                pass

        selected_collection: SymbolCollectionModel = (
            self.saved_symbols_list_box.itemData(index)
        )

        if selected_collection is not None:
            self._clear_surfaces()
            self._current_collection = selected_collection
            dir_path = self._collections_repository.get_collections_persistence_dir().joinpath(
                selected_collection.directory
            )
            if not dir_path.is_dir():
                self.logger.warning(f"Símbolos de colección {selected_collection.collection_name} no encontrados. Problema al leer directorio {dir_path}")
                QMessageBox.warning(self, "Imágenes no encontradas", "No se encontraron los símbolos de la colección. Es posible que el directorio donde estaban se haya movido, modificado o eliminado. ")
            else:
                for path in dir_path.iterdir():
                    char_image_path = path.absolute()
                    char = path.name.replace(path.suffix, "")
                    drop_surface = self._drop_surfaces.get(char, None)
                    if drop_surface:
                        drop_surface.set_symbol(char_image_path)
                self._load_symbols_on_mapper()
            self._collections_repository.set_to_saved()
            self.symbols_changed.emit()
            self.logger.info(f"Colección cargada: {selected_collection.collection_name}")
        else:
            pass

    def select_collection_by_name(self, collection_name):
        match = next((
            (index, collection)
            for index, collection in enumerate(self._collections)
            if collection.collection_name == collection_name), None
        )
        if not match:
            self._clear_collection()
            return None
            
        index, collection = match
        self.saved_symbols_list_box.setCurrentIndex(index)
        self.logger.info(f"Colección cargada: {collection.collection_name}")
        return collection

    def is_empty(self):
        for surface in self._drop_surfaces.values():
            if surface.has_symbol():
                return False
        return True

    ## Falta el caso en que las superficies estén vacías y se haya modificado una
    def _on_create_collection(self):
        if not self.is_empty() and not self._collections_repository.is_saved():
            button = self._unsaved_changes_messagebox()
            if button == QMessageBox.StandardButton.Cancel:
                return
            elif button == QMessageBox.StandardButton.Yes:
                self._on_save_collection()
            elif button == QMessageBox.StandardButton.No:
                self._collections_repository.set_to_saved()
        self._clear_collection()

    def _unsaved_changes_messagebox(self):
        """Abre una ventana para consultar si guardar o no cambios no guardados"""
        button = QMessageBox.question(
            self,
            "Cambios no guardados",
            "Hay cambios sin guardar. ¿Quieres guardarlos?",
            buttons=QMessageBox.StandardButton.No
            | QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.Cancel,
        )
        return button

    def _clear_collection(self):
        self.saved_symbols_list_box.setCurrentIndex(-1)
        self._current_collection = {}
        self._clear_surfaces()
        self._symbol_mapper.clear_map()
        self.symbols_changed.emit()

    def _clear_surfaces(self):
        for surface in self._drop_surfaces.values():
            surface.clear()

    def _on_rename_collection(self):

        ## Acá voy a cambiar también el nombre del directorio, así que hay que aplicar una corrección de texto
        if self._current_collection:
            get_name_widget = QWidget(self)
            new_name, ok = QInputDialog.getText(
                get_name_widget,
                "Nombre de la colección",
                "Ponle un nombre a tu colección:",
            )
            if ok:
                new_dir_name = self._generate_dir_name(new_name)

                saved_collection = self._collections_repository.findByName(new_name)
                while saved_collection:
                    new_name, ok = QInputDialog.getText(
                        get_name_widget,
                        "Nombre de la colección",
                        f"El nombre {new_name} ya está guardado, elige otro:",
                    )
                    if ok:
                        saved_collection = self._collections_repository.findByName(
                            new_name
                        )
                        new_name
                    else:
                        return
                collection = SymbolCollectionModel(
                    collection_name=new_name, directory=new_dir_name
                )
                try:
                    old_name = self._current_collection.collection_name
                    self._collections_repository.update(
                        old_name, collection
                    )
                    self._current_collection = collection
                    combobox_idx = self.saved_symbols_list_box.currentIndex()
                    self.saved_symbols_list_box.setItemText(combobox_idx, new_name)
                    self.saved_symbols_list_box.setItemData(combobox_idx, collection)
                    self.logger.info(f"Colección renombrada: '{old_name}' -> '{new_name}'")
                except StorageError as error:
                    QMessageBox.critical(
                        self, "Error al renombrar", "Ocurrió un error al renombrar la colección. Comprueba que tienes permisos de escritura."
                    ) 
                    self.logger.error(f"Fallo al renombrar la colección '{old_name} a '{new_name}' | {error}")

    def _on_save_collection(self):
        if not self._current_collection:
            self._on_save_collection_as()
        elif self._collections_repository.is_saved():
            pass
        else:
            button = QMessageBox.question(
                self,
                "Guardar cambios",
                "¿Confirmas que quieres guardar los cambios?",
                buttons=QMessageBox.StandardButton.No | QMessageBox.StandardButton.Yes,
            )
            if button == QMessageBox.StandardButton.Yes:
                self._save_collection()
                self._on_collection_selected(self.saved_symbols_list_box.currentIndex())

    def _save_collection(self):
        collection_dir = (
            self._collections_repository._collections_persistence_dir.joinpath(
                self._current_collection.directory
            )
        )
        try:
            if not collection_dir.is_dir():
                collection_dir.mkdir(parents=True, exist_ok=True)
            files = {
                item.name.split(".")[0]: item.name for item in collection_dir.iterdir()
            }
            for surface in self._drop_surfaces.values():
                old_filename = files.get(surface.symbol_name, None)
                if not surface.has_symbol():
                    if old_filename:
                        Path(collection_dir.joinpath(old_filename)).unlink(missing_ok=True)
                else:
                    new_filename = collection_dir.joinpath(surface.get_file_name())
                    pixmap = surface.pixmap
                    bytes_array = QByteArray()
                    buffer = QBuffer(bytes_array)
                    buffer.open(QIODevice.OpenModeFlag.WriteOnly)
                    pixmap.save(buffer, surface.get_format()) 
                    buffer.close()
                    self._file_service.save(new_filename, bytes_array)
                    surface.set_symbol(new_filename)
            self._collections_repository.set_to_saved()
            self.logger.info(f"Colección guardada: {self._current_collection.collection_name}")
        except (OSError, StorageError) as error:
            QMessageBox.critical(
                self, f"Error al guardar", f"Ocurrió un error al guardar la colección '{self._current_collection.collection_name}'. Comprueba que tienes espacio en disco y permisos de escritura."
            ) 
            self.logger.error(f"Fallo al guardar la colección '{self._current_collection.collection_name}' | {error}")

        except Exception as error:
            QMessageBox.critical(
                self, "Error misterioso al guardar", "Ocurrió un error misterioso al guardar la colección."
            ) 
            self.logger.error(f"Fallo misterioso al guardar '{self._current_collection.collection_name}' en el directorio {self._current_collection.directory}. | {error}")
    def _on_save_collection_as(self):  ## Repasar

        get_name_widget = QWidget(self)
        new_name, ok = QInputDialog.getText(
            get_name_widget, "Nombre de la colección", "Ponle un nombre a tu colección:"
        )

        if not ok:
            return

        saved_collection = self._collections_repository.findByName(new_name)
        while saved_collection:
            new_name, ok = QInputDialog.getText(
                get_name_widget,
                "Nombre de la colección",
                f"El nombre {new_name} ya está guardado, elige otro:",
            )
            if ok:
                saved_collection = self._collections_repository.findByName(new_name)
                new_name
            else:
                return

        new_dir = self._generate_dir_name(new_name)
        new_collection = SymbolCollectionModel(
            collection_name=new_name, directory=new_dir
        )
        collection_dir = (
            self._collections_repository._collections_persistence_dir.joinpath(new_dir)
        )
        try:
            if not collection_dir.is_dir():
                collection_dir.mkdir(parents=True, exist_ok=True)
            for surface in self._drop_surfaces.values():
                if surface.has_symbol():
                    new_filename = collection_dir.joinpath(surface.get_file_name())
                    pixmap = surface.pixmap
                    bytes_array = QByteArray()
                    buffer = QBuffer(bytes_array)
                    buffer.open(QIODevice.OpenModeFlag.WriteOnly)
                    pixmap.save(buffer, surface.get_format()) 
                    buffer.close()
                    self._file_service.save(new_filename, bytes_array)
                    surface.set_symbol(new_filename)            
            self._collections_repository.save(new_collection)
            self.saved_symbols_list_box.addItem(
                new_collection.collection_name, new_collection
            )
            self.saved_symbols_list_box.setCurrentIndex(
                self.saved_symbols_list_box.count() - 1
            )
            self._collections_repository.set_to_saved()
            self.logger.info(f"Colección guardada como: {new_name}")
        except (OSError, StorageError) as error:
            QMessageBox.critical(
                self, "Error al guardar", "Ocurrió un error al guardar la colección. Comprueba que tienes espacio en disco y permisos de escritura."
            ) 
            self.logger.error(f"Fallo al guardar la colección '{new_name}' en el directorio {collection_dir} | {error}")

        except Exception as error:
            QMessageBox.critical(
                self, "Error misterioso al guardar", "Ocurrió un error misterioso al guardar la colección."
            ) 
            self.logger.error(f"Fallo misterioso al guardar '{new_name}'en el directorio {collection_dir} | {error}")
            
    def _on_delete_collection(self):
        if not self._current_collection:
            return
        button = QMessageBox.question(
            self,
            "Guardar cambios",
            f"¿Confirmas que quieres eliminar la colección '{self._current_collection.collection_name}'?",
            buttons=QMessageBox.StandardButton.No | QMessageBox.StandardButton.Yes,
        )
        if button == QMessageBox.StandardButton.Yes:
            try:
                removed_collectionName =  self._current_collection.collection_name
                removed_directory =  self._current_collection.directory
                removed_directory_path = self._collections_repository.get_collections_persistence_dir().joinpath(removed_directory)
                self._collections_repository.delete(
                    removed_collectionName
                )
                self.saved_symbols_list_box.removeItem(
                    self.saved_symbols_list_box.currentIndex()
                )
                self._clear_collection()
                self.logger.info(f"Colección eliminada: {removed_collectionName}. Directorio de colección removido: {removed_directory_path}" )
            except DirectoryRemovalError as e:
                QMessageBox.critical(
                    self, "Error al eliminar", f"Ocurrió un error al eliminar la colección '{removed_collectionName}'. Comprueba que tienes permisos de escritura."
                ) 
                self.logger.error(f"Fallo al eliminar la colección '{removed_collectionName}' con directorio '{removed_directory_path}' | {error}")

            except Exception as error:
                QMessageBox.critical(
                    self, "Error misterioso al eliminar", f"Ocurrió un error misterioso al eliminar la colección '{removed_collectionName}'."
                ) 
                self.logger.error(f"Fallo misterioso al eliminar la colección '{removed_collectionName}' con directorio '{removed_directory_path}' | {error}")
        return

    def _generate_dir_name(self, collection_name: str) -> str:
        """Genera un nombre de directorio a partir de un string. Remueve y reemplaza caracteres no permitidos para nombres de directorios."""
        nfkd = unicodedata.normalize("NFKD", collection_name)
        sin_tildes = "".join([c for c in nfkd if not unicodedata.combining(c)])
        clean_name = re.sub(r"[^a-zA-Z0-9_.-]", "_", sin_tildes)
        clean_name = re.sub(r"_+", "_", clean_name).strip("_")
        timed_name = f"{clean_name}{int(datetime.now().timestamp()*1000)}"
        return timed_name.lower()

    def _load_symbols_on_mapper(self):
        """Limpia los pixmap del Symbol Maper y le asigna los pixmap de cada Drop Surface"""
        self._symbol_mapper.clear_map()
        for char, surface in self._drop_surfaces.items():
            self._symbol_mapper.set_pixmap(char, surface.pixmap)

    def _load_collections_list(self):
        self._collections = self._collections_repository.findAll()

    def _setup_toolbar(self):
        toolbar = QToolBar("Barra de Herramientas Symbols", self)
        self.addToolBar(Qt.ToolBarArea.LeftToolBarArea, toolbar)

        self._create_collection_action = QAction("Nueva colección", self)
        self._create_collection_action.triggered.connect(self._on_create_collection)

        self._save_collection_action = QAction("Guardar cambios", self)
        self._save_collection_action.triggered.connect(self._on_save_collection)

        self._save_collection_as_action = QAction("Guardar como nueva colección", self)
        self._save_collection_as_action.triggered.connect(self._on_save_collection_as)

        self._rename_collection_action = QAction("Renombrar", self)
        self._rename_collection_action.triggered.connect(self._on_rename_collection)

        self._delete_collection_action = QAction("Eliminar Colección", self)
        self._delete_collection_action.triggered.connect(self._on_delete_collection)

        saved_symbols_list_label = QLabel("Colecciones", self)
        self.saved_symbols_list_box = QComboBox(self)

        self.saved_symbols_list_box.setPlaceholderText("Selecciona una colección...")
        self.saved_symbols_list_box.setCurrentIndex(-1)
        self.saved_symbols_list_box.setSizeAdjustPolicy(
            QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon
        )
        self.saved_symbols_list_box.setMinimumContentsLength(15)
        self.saved_symbols_list_box.setMaximumWidth(200)
        self.saved_symbols_list_box.setSizePolicy(
            QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Fixed
        )
        for collection in self._collections:
            self.saved_symbols_list_box.addItem(collection.collection_name, collection)

        self.saved_symbols_list_box.currentIndexChanged.connect(
            self._on_collection_selected
        )
        toolbar.addAction(self._create_collection_action)
        toolbar.addSeparator()
        toolbar.addAction(self._rename_collection_action)
        toolbar.addAction(self._save_collection_action)
        toolbar.addAction(self._save_collection_as_action)
        toolbar.addAction(self._delete_collection_action)
        toolbar.addSeparator()
        toolbar.addWidget(saved_symbols_list_label)
        toolbar.addWidget(self.saved_symbols_list_box)

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
            drop_clear_button.clicked.connect(
                lambda: self._collections_repository.set_to_unsaved()
            )
            drop_layout.addWidget(drop_clear_button)

            drop_container.setFixedSize(self._drop_surface_size)

            drop_container.setObjectName(self._drop_container_object_name)
            drop_surface.setObjectName(self._drop_container_surface_object_name)
            drop_surface.image_dropped.connect(
                lambda: self._collections_repository.set_to_unsaved()
            )

            row, col = idx // self._columns_count, idx % self._columns_count
            self._main_layout.addWidget(drop_container, row, col)

            self._drop_surfaces[character] = drop_surface
