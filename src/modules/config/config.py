class Config:
    WIDTH, HEIGHT = 768, 1024
    ASSETS_DIR = "assets"
    DEFAULT_ASSETS_DIR = "default_set"
    APP_VERSION = "0.1.1"
    UNTITLED_DEFAULT_FILENAME = "sintitulo"
    MAIN_WINDOW_TITLE = "Editor de Escrituras Simbólicas"
    # PROJECT_ROOT = Path(sys.argv[0]).resolve().parent.parent
    # ASSETS_PATH = PROJECT_ROOT / ASSETS_DIR

    CHARACTERS = ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "ñ", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z"]

def load_config():
    config = Config()
    return config
