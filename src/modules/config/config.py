class Config:
    WIDTH, HEIGHT = 1024, 768
    ASSETS_DIR = "assets"
    DEFAULT_ASSETS_DIR = "default_set"
    APP_VERSION = "0.1.1"
    UNTITLED_DEFAULT_FILENAME = "sintitulo"
    MAIN_WINDOW_TITLE = "Editor de Escrituras Simbólicas"
    # PROJECT_ROOT = Path(sys.argv[0]).resolve().parent.parent
    # ASSETS_PATH = PROJECT_ROOT / ASSETS_DIR


def load_config():
    config = Config()
    return config
