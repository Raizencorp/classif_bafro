import os
import rasterio as io
import numpy as np
from time import time
from Classif_BAFRO import classif_BAFRO
from Classif_Ombre import classif_Ombre
from Fuse import fuse
from skimage import filters

model_BAFRO =   "/foo/model_BAFRO.sav"
model_Ombre =   "/foo/model_Ombre.pkl"

i = 0
time_all = 0

for region in ("u11", "u12"):
    time_start = time()
    print("Working on : " + region)
    
    ########## Laplacev2 #########
    print("Create laplacev2")
    ir = io.open("/foo/" + region + "/D032_2019_" + region + "_b100_irc.tif")
    ir = ir.read()

    img = io.open("/foo/" + region + "/D032_2019_" + region + "_b100_rvb.tif")
    rgb = img.read()

    b = np.zeros((4, rgb.shape[1], rgb.shape[2]))
    b[0] = rgb[0]
    b[1] = rgb[0]
    b[2] = rgb[1]
    b[3] = ir[0]

    result = filters.laplace(b)

    ir = None
    rgb = None

    with io.open("/foo/" + region + "/laplacev2_" + region + ".tif",
             'w',
             driver='GTiff',
             height=result.shape[1],
             width=result.shape[2],
             count=result.shape[0],
             dtype=np.float64,
             transform=img.transform,
             crs=img.crs
             ) as dst:
        dst.write(result)
    b = None
    
    ########## Classif BAFRO #########
    print("Classif BAFRO")
    classif_BAFRO(region, model_BAFRO)

    ########## Classif Ombre #########
    print("Classif Ombre")
    classif_Ombre(region, model_Ombre)

    ########## Fuse #########
    print("Fuse 1")
    fuse(region, 1)

    ########## Polygonize #########
    print("Polygonize")
    cmd = "gdal_polygonize.py /foo/" + region + "/Fuse_" + region + ".tif /foo/" + region + "/seg_" + region + ".tif"
    os.system(cmd)

    ########## Pre Code IGN #########
    print("Fuse 2")
    fuse(region, 2)

    ########## Pre Code Interne #########
    print("Fuse 3")
    fuse(region, 0)

    i += 1
    time_all += (time() - time_start)
    print("Region: " + region + " en " + str(time() - time_start) + "s")

print("Done Boss !")
print(str(i) + " region en " + str(time_all) + "s")
