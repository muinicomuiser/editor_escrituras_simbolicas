import logging

from platformdirs import user_config_dir
class Config:
    WIDTH, HEIGHT = 768, 980
    APP_VERSION = "1.0.1"
    APP_NAME = "EscriturasSimbolicas"
    APP_AUTOR = "Nicolás Donoso (ig: @niconicodonoso @nicosodonoso - gh: muinicomuiser)"
    UNTITLED_DEFAULT_FILENAME = "sintitulo"
    MAIN_WINDOW_TITLE = "Editor de Escrituras Simbólicas"

    CHARACTERS = {
        "single": list("abcdefghijklmnñopqrstuvwxyz"),
        "compound": ["ch", "ll"],
    }
    LOG_LEVEL = "INFO"
    LOG_FILENAME = "escrituras_simbolicas.log"

    @property
    def CONFIG_DIR():
        return user_config_dir(
        appname=Config.APP_NAME
        # appauthor=self.APP_AUTOR
    )

def load_config():
    config = Config()
    return config
