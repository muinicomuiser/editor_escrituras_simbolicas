from dataclasses import dataclass
import os
from pathlib import Path
import sys
from modules.config.config import load_config
from modules.persistence.projects_service import ProjectsService
from modules.persistence.file_service import FilesService
from modules.persistence.symbols_collections_repository import SymbolsCollectionRepository
from modules.symbols.collections_service import CollectionsService
from modules.symbols.symbol_mapper import SymbolMapper
from modules.symbols.symbol_selector_widget import SymbolSelectorWindow
from modules.editor_widget import EditorWidget
from modules.main_window import MainWindow

@dataclass
class AppContext:
    main_window: MainWindow

def bootstrap_application() -> AppContext:

    config = load_config()
    
    # 1. Configuración de rutas globales
    collections_dir = Path(
        getattr(sys, "_MEIPASS", os.path.abspath(".")), "data/simbolos"
    )
    collections_catalog_file = collections_dir.joinpath(
        "symbol_collections.json"
        )

    # 2. Repositorios (Infraestructura)
    files_service = FilesService()
    collections_repository = SymbolsCollectionRepository(
        collections_dir=collections_dir, 
        collections_catalog_file=collections_catalog_file
        )

    # 3. Servicios (Dominio / Aplicación)
    projects_service = ProjectsService()
    symbol_mapper = SymbolMapper()
    collections_service = CollectionsService(
        collections_repository=collections_repository,
        file_service=files_service
    )
    
    # 4. Presentación (UI)
    collections_editor = SymbolSelectorWindow(
        symbol_mapper=symbol_mapper,
        collections_service=collections_service
        )
    text_editor = EditorWidget(
        config=config,
        symbol_mapper=symbol_mapper
        )
    main_window = MainWindow(
        config=config,
        collections_editor=collections_editor,
        text_editor=text_editor,
        projects_service=projects_service
    )
   
    return AppContext(
        main_window=main_window
    )