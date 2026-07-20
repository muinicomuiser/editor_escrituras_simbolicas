from pathlib import Path
from modules.enum.paper_sizes import PaperSizes

class Config:
    WIDTH, HEIGHT = 1024, 768    
    ASSETS_DIR = "assets"
    DEFAULT_ASSETS_DIR = "default_set"
    # PROJECT_ROOT = Path(sys.argv[0]).resolve().parent.parent
    # ASSETS_PATH = PROJECT_ROOT / ASSETS_DIR


def load_config():
    config = Config()
    return config