from PIL import Image
import numpy as np

imagen = Image.open("./pruebas/simbolos/a.jpg", "r")

target = np.array([255, 255, 255])
margen = 20
rango_superior = target + margen
rango_inferior = target - margen
imagen_array = np.array(imagen.convert("RGB"))

mask = ((imagen_array[:, :, 0] >= rango_inferior[0])
        & (imagen_array[:, :, 0] <= rango_superior[0])
        & (imagen_array[:, :, 1] <= rango_superior[1])
        & (imagen_array[:, :, 1] <= rango_superior[1])
        & (imagen_array[:, :, 2] <= rango_superior[2])
        & (imagen_array[:, :, 2] <= rango_superior[2])
        )
imagen_array[:, :, :] = np.mean(imagen_array, axis=2, keepdims=True)
# print(imagen_array)
imagen_bn = np.array(Image.fromarray(imagen_array).convert("RGBA"))
imagen_bn[mask, 3] = 0
imagen_bn[:,:,0] -= imagen_bn[:,:,0] // 3 
imagen_bn[:,:,1] -= imagen_bn[:,:,1] // 3 
imagen_bn[:,:,2] -= imagen_bn[:,:,2]  // 3 
imagen_png = Image.fromarray(imagen_bn).convert("RGBA")


imagen_png.show()
## Promedio con np.array.mean()
# array = np.array([[22, 55, 89], [4, 4,178]])
# print(imagen_array)