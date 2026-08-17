class Config:
    WIDTH, HEIGHT = 768, 980
    APP_VERSION = "0.2.0"
    UNTITLED_DEFAULT_FILENAME = "sintitulo"
    MAIN_WINDOW_TITLE = "Editor de Escrituras Simbólicas"

    CHARACTERS = {
        "single": list("abcdefghijklmnñopqrstuvwxyz"),
        "compound": ["ch", "ll"],
    }


def load_config():
    config = Config()
    return config
