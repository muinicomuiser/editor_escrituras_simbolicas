from enum import Enum


class PaperSizes(Enum):
    A4_300PPI = (2480, 3508)
    A4_150PPI = (1240, 1754)
    A4_72PPI = (595, 842)
    OFICIO_300PPI = (2550, 3900)
    OFICIO_150PPI = (1240, 1950)
    OFICIO_72PPI = (612, 936)
    CARTA_300PPI = (2550, 3300)
    CARTA_150PPI = (1275, 1650)
    CARTA_72PPI = (612, 792)