from itertools import chain
import uuid
from PySide6.QtCore import QSize, QThreadPool, Signal, Qt
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
from modules.symbols.collections_service import CollectionsService
from modules.symbols.symbol_mapper import SymbolMapper
from modules.shared.models.symbol_collection_model import SymbolCollectionModel
from modules.shared.generic_workers import ServiceCallWorker
from modules.utils.logger import get_logger
from modules.exceptions.exceptions import StorageError, DirectoryRemovalError, DirectoryNotFoundError

class SymbolSelectorWindow(QMainWindow):
    symbols_changed = Signal()

    def __init__(self, symbol_mapper: SymbolMapper, collections_service: CollectionsService, parent=None):
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
        self._workers_data = {
            "total": 0,
            "count": 0,
            "batch_id": None
        }

        # Contenedores principales
        self._container = QWidget()
        self._main_layout = QGridLayout(self._container)
        self._scroll_area = QScrollArea()
        self._scroll_area.setWidgetResizable(True)
        self._scroll_area.setWidget(self._container)
        self.setCentralWidget(self._scroll_area)

        # Persistencia
        self._collections_service = collections_service
        self._collection_saved = True

        # Setup de componentes
        self._load_collections_list()
        self._setup_toolbar()
        self._setup_drop_containers()

        # style
        self.setWindowTitle("Editor de colección de símbolos")
        self.setMinimumSize(self._base_size)

        self.logger = get_logger(self.__class__.__name__)
        self.logger.info(f"Módulo Iniciado")           


    def get_current_collection_name(self):
        return (
            self._current_collection.collection_name if self._current_collection else ""
        )

    def set_to_unsaved(self):
        self._collection_saved = False

    def set_to_saved(self):
        self._collection_saved = True
    
    def is_empty(self):
        for surface in self._drop_surfaces.values():
            if surface.has_symbol():
                return False
        return True
    
    def closeEvent(self, event):
        if not self.is_empty() and not self._collection_saved:
            button = self._unsaved_changes_messagebox()
            if button == QMessageBox.StandardButton.Cancel:
                event.ignore()
                return
            elif button == QMessageBox.StandardButton.Yes:
                if self._current_collection:
                    symbols_data = self._generate_symbols_data()
                    self._collections_service.save_collection(self._current_collection, symbols_data)                
                    self.set_to_saved()
                    self._on_collection_selected(self.saved_symbols_list_box.currentIndex())
                else:
                    self._on_save_collection_as()
                    self.set_to_saved()
            elif button == QMessageBox.StandardButton.No:
                self._clear_surfaces()
                for value in self.characters.values():
                    for char in value:
                        self._drop_surfaces[char].pixmap = self._symbol_mapper.get_pixmap(char)
                self.set_to_saved()
        self._workers_data["batch_id"] = None
        event.accept()

    def _on_collection_selected(self, index: int):
        if index < 0:
            return

        if not self._collection_saved:
            button = self._unsaved_changes_messagebox()
            if button == QMessageBox.StandardButton.Cancel:
                return
            elif button == QMessageBox.StandardButton.Yes:
                self._on_save_collection()
                # await self._on_save_collection()
            elif button == QMessageBox.StandardButton.No:
                pass

        selected_collection: SymbolCollectionModel = (
            self.saved_symbols_list_box.itemData(index)
        )

        if selected_collection is not None:
            self._clear_surfaces()
            self._current_collection = selected_collection
            try:
                symbols_paths = self._collections_service.get_collection_imagepaths(selected_collection)
                batch_id = str(uuid.uuid4())
                self._workers_data["batch_id"] = batch_id
                self._workers_data["total"] = len(symbols_paths)
                for char, path in symbols_paths.items():
                    worker = ServiceCallWorker(
                        service_function=self._collections_service.get_symbol,
                        element_id=char,
                        image_path=path
                    )

                    worker.signals.finished.connect(lambda image_bytes, element_id: self._worker_done(element_id, batch_id, image_bytes))
                    worker.signals.error.connect(lambda error, element_id: self._worker_done(element_id, batch_id))
                    QThreadPool.globalInstance().start(worker)

            except StorageError as error:
                self.logger.error(f"Fallo al leer los símbolos de colección '{selected_collection.collection_name}' | {error}")
                QMessageBox.warning(self, "Imágenes no encontradas", f"No se pudo leer símbolos de la colección '{selected_collection.collection_name}'. Es posible que estén corruptos o no tengas permisos para acceder a ellos. ")
            except DirectoryNotFoundError as error:
                self.logger.warning(f"Símbolos de colección {selected_collection.collection_name} no encontrados. Problema al leer directorio '{selected_collection.directory}' | {error}")
                QMessageBox.warning(self, "Directorio no encontrado", "No se encontraron los símbolos de la colección. Es posible que el directorio donde estaban se haya movido, modificado o eliminado. ")
            except Exception as error:
                QMessageBox.warning(
                    self, "Error misterioso al cargar la colección", "Ocurrió un error misterioso al cargar los archivos de la colección. No se pudieron leer."
                ) 
                self.logger.error(f"Fallo misterioso al cargar '{self._current_collection.collection_name}' desde el directorio {self._current_collection.directory}. | {error}")
            finally:
                self._load_symbols_on_mapper()
                self.set_to_saved()
                self.symbols_changed.emit()
                self.logger.info(f"Colección cargada: {selected_collection.collection_name}")
        else:
            pass

    def _worker_done(self, char: str, batch_id: str, image_bytes: bytes | None):
        if batch_id != self._workers_data["batch_id"]:
            return
        self._workers_data["count"] += 1
        if image_bytes:
            self._drop_surfaces[char].set_symbol_bytes(image_bytes)
        if self._workers_data["count"] >= self._workers_data["total"]:
            self._load_symbols_on_mapper()
            self.set_to_saved()
            self.symbols_changed.emit()
            self.logger.info(f"Colección cargada: {self._current_collection.collection_name}") 


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
        self.set_to_saved()
        self.logger.info(f"Colección cargada: {collection.collection_name}")
        return collection

    def _on_create_collection(self):
        if not self.is_empty() and not self._collection_saved:
            button = self._unsaved_changes_messagebox()
            if button == QMessageBox.StandardButton.Cancel:
                return
            elif button == QMessageBox.StandardButton.Yes:
                if self._current_collection:
                    self._on_save_collection()
                else:
                    self._on_save_collection_as()
            elif button == QMessageBox.StandardButton.No:
                self.set_to_saved()
        self._clear_collection()

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
        if self._current_collection:
            new_name = self._ask_collection_name_loop()
            if not new_name:
                return

            collection = SymbolCollectionModel(
                collection_name=new_name, directory=self._collections_service.generate_dir_name(new_name)
            )
            try:
                old_name = self._current_collection.collection_name
                self._collections_service.update_collection(
                    old_name, collection
                )
                self.set_to_saved()
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
        elif self._collection_saved:
            pass
        else:
            button = QMessageBox.question(
                self,
                "Guardar cambios",
                "¿Confirmas que quieres guardar los cambios?",
                buttons=QMessageBox.StandardButton.No | QMessageBox.StandardButton.Yes,
            )
            if button == QMessageBox.StandardButton.Yes:
                symbols_data = self._generate_symbols_data()
                try:
                    self._collections_service.save_collection(self._current_collection, symbols_data)                
                    self.set_to_saved()
                    self._on_collection_selected(self.saved_symbols_list_box.currentIndex())
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
    
    def _on_save_collection_as(self):
        new_name = self._ask_collection_name_loop()
        if not new_name:
            return

        new_collection = SymbolCollectionModel(
            collection_name=new_name, directory=self._collections_service.generate_dir_name(new_name)
        )
        symbols_data = self._generate_symbols_data()
        try:
            self._collections_service.save_collection(new_collection, symbols_data)
            self.set_to_saved()
            self.saved_symbols_list_box.addItem(
                new_collection.collection_name, new_collection
            )
            self.saved_symbols_list_box.setCurrentIndex(
                self.saved_symbols_list_box.count() - 1
            )
            self.logger.info(f"Colección guardada como: {new_name}")
        except (OSError, StorageError) as error:
            QMessageBox.critical(
                self, "Error al guardar", "Ocurrió un error al guardar la colección. Comprueba que tienes espacio en disco y permisos de escritura."
            ) 
            self.logger.error(f"Fallo al guardar la colección '{new_name}' en el directorio {new_collection.directory} | {error}")

        except Exception as error:
            QMessageBox.critical(
                self, "Error misterioso al guardar", "Ocurrió un error misterioso al guardar la colección."
            ) 
            self.logger.error(f"Fallo misterioso al guardar '{new_name}'en el directorio {new_collection.directory} | {error}")
            
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
                deleted_collection = self._current_collection
                self._collections_service.delete_collection(deleted_collection)
                self.saved_symbols_list_box.removeItem(
                    self.saved_symbols_list_box.currentIndex()
                )
                self._clear_collection()
                self.set_to_saved()
                self.logger.info(f"Colección eliminada: {deleted_collection.collection_name}. Directorio de colección removido: {deleted_collection.directory}" )
            except DirectoryRemovalError as error:
                QMessageBox.critical(
                    self, "Error al eliminar símbolos", f"Ocurrió un error al eliminar los símbolos de la colección '{deleted_collection.collection_name}'. Comprueba que tienes permisos de escritura."
                ) 
                self.logger.error(f"Fallo al eliminar la colección '{deleted_collection.collection_name}' con directorio '{deleted_collection.directory}' | {error}")
            except StorageError as error:
                QMessageBox.critical(
                    self, "Error al eliminar colección", f"Ocurrió un error al eliminar la colección '{deleted_collection.collection_name}'. Comprueba que tienes permisos de escritura."
                ) 
                self.logger.error(f"Fallo al eliminar la colección '{deleted_collection.collection_name}' con directorio '{deleted_collection.directory}' | {error}")

            except Exception as error:
                QMessageBox.critical(
                    self, "Error misterioso al eliminar", f"Ocurrió un error misterioso al eliminar la colección '{deleted_collection.collection_name}'."
                ) 
                self.logger.error(f"Fallo misterioso al eliminar la colección '{deleted_collection.collection_name}' con directorio '{deleted_collection.directory}' | {error}")
        return
    
    def _load_symbols_on_mapper(self):
        """Limpia los pixmap del Symbol Maper y le asigna los pixmap de cada Drop Surface"""
        self._symbol_mapper.clear_map()
        for char, surface in self._drop_surfaces.items():
            self._symbol_mapper.set_pixmap(char, surface.pixmap)

    def _load_collections_list(self):
        self._collections = self._collections_service.get_collections_list()
    
    def _generate_symbols_data(self):
        symbols_data = {}
        for surface in self._drop_surfaces.values():
            symbols_data[surface.get_symbol_name()] = surface.get_symbol_bytes()        
        return symbols_data

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

    def _ask_collection_name_loop(self) -> str | None:
        get_name_widget = QWidget(self)
        new_name, ok = QInputDialog.getText(
            get_name_widget, "Nombre de la colección", "Ponle un nombre a tu colección:"
        )

        if not ok:
            return

        saved_collection = self._collections_service.find_collection_by_name(new_name)
        while saved_collection:
            new_name, ok = QInputDialog.getText(
                get_name_widget,
                "Nombre de la colección",
                f"El nombre '{new_name} 'ya está guardado, elige otro:",
            )
            if ok:
                saved_collection = self._collections_service.find_collection_by_name(new_name)
            else:
                return
        return new_name

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
                lambda: self.set_to_unsaved()
            )
            drop_layout.addWidget(drop_clear_button)

            drop_container.setFixedSize(self._drop_surface_size)

            drop_container.setObjectName(self._drop_container_object_name)
            drop_surface.setObjectName(self._drop_container_surface_object_name)
            drop_surface.image_dropped.connect(
                lambda: self.set_to_unsaved()
            )

            row, col = idx // self._columns_count, idx % self._columns_count
            self._main_layout.addWidget(drop_container, row, col)

            self._drop_surfaces[character] = drop_surface
