from PIL import Image
from pathlib import Path

# Script para leer los archivos de un directorio,
# recortar toda el área exterior transparente de los archivos .png
# y guardarlos en otro directorio

p = Path("./pruebas/assets_vale")
destino = Path("assets_vale_crop")
for children in p.iterdir():
    if str(children).endswith(".png"):
        with Image.open(children) as im:
            bounding_box = im.getbbox()
            croped = im.crop(bounding_box)
            filename = children.parent / destino / f"{children.name}"
            # print(filename)
            croped.save(filename)
            # print(children.parent / f"crop-{children.name}")
            # print(children.name)
            # print(children.stem)