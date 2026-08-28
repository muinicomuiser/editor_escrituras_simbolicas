# from dataclasses import dataclass
# from pathlib import Path
# from PySide6.QtWidgets import QApplication

# import argparse
# import signal
# import sys
# import os
# import platform
# from PySide6.QtCore import Qt
# from PySide6.QtWidgets import QApplication, QStyleFactory
# from modules.config.config import load_config
# from modules.main_window import MainWindow
# from style.stylesheet import stylesheet
# from modules.utils.logger import get_logger, setup_logger

# from modules.main_window import MainWindow

# from infrastructure.repositories import JsonCatalogRepository, DiskImageRepository
# from core.services import CollectionsService, ProjectsService
# from ui.windows import MainWindow

# @dataclass
# class AppContext:
#     """Contenedor simple de referencias vivas de la aplicación."""
#     main_window: MainWindow
#     collections_service: CollectionsService

# def bootstrap_application() -> AppContext:
#     """Composition Root: Construye la pila completa de dependencias."""
    
#     # 1. Configuración de rutas globales
#     base_dir = Path.home() / ".local" / "share" / "mi_app"
    
#     # 2. Repositorios (Infraestructura)
#     catalog_repo = JsonCatalogRepository(config_path=base_dir / "catalog.json")
#     image_repo = DiskImageRepository(storage_path=base_dir / "images")
    
#     # 3. Servicios (Dominio / Aplicación)
#     collections_service = CollectionsService(
#         catalog_repo=catalog_repo,
#         image_repo=image_repo
#     )
#     projects_service = ProjectsService(catalog_repo=catalog_repo)
    
#     # 4. Presentación (UI)
#     main_window = MainWindow(
#         collections_service=collections_service,
#         projects_service=projects_service
#     )
    
#     return AppContext(
#         main_window=main_window,
#         collections_service=collections_service
#     )