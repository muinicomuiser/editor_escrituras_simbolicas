import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import sys
from typing import Optional
from modules.config.config import Config
from modules.config.config import load_config

def setup_logger(
        level: Optional[str] = None,
        log_file: Optional[str] = None
):
    config = load_config()    
    log_level = level or config.LOG_LEVEL
    format_string = (
        "%(asctime)-24s - %(name)-28s - %(levelname)-8s - "
        "%(filename)s:%(lineno)d - %(message)s"
    )    
    # Configurar el logger raíz
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format=format_string,
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[]
    )
    
    # Handler para consola
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level.upper()))
    console_formatter = logging.Formatter(format_string)
    console_handler.setFormatter(console_formatter)    

    file_handler = None

    if log_file:
        path = Path(log_file)
        path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = RotatingFileHandler(log_file)
        file_handler.setLevel(logging, log_level.upper())
        file_formater = logging.Formatter(format_string)
        file_handler.setFormatter(file_formater)

    logger = logging.getLogger()
    logger.handlers.clear()
    logger.addHandler(console_handler)
    if file_handler:
        logger.addHandler(file_handler)


def get_logger(name: str):
    if not logging.getLogger().handlers:
        setup_logger()
    logger = logging.getLogger(name)
    return logger
