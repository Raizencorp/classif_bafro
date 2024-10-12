import rasterio as io
import numpy as np

for region in ("n10", "n11", "n12", "n13", "n14", "n15", "n16", "n17", "n18", "n19", "n20", 
               "u2", "u6", "u7", "u9", "u11", "u12", "u13", "u14", "u15", "u16", "u17", "u18", 
               "u19", "u20", "v4", "v6", "v7", "v10", "v11", "v12", "v13", "v14", "v15", 
               "v16", "v17", "v18", "v19", "v20", "v21", "v22"):

    print("Create 5b img")
    mns = "/foo/" + region + "/mns.tif"
    mnt = "/foo/" + region + "/D032_2019_" + region + "_b100_mnt.tif"

    ir = io.open("/foo/" + region + "/D032_2019_" + region + "_b100_irc.tif")
    ir = ir.read()

    img = io.open("/foo/" + region + "/D032_2019_" + region + "_b100_rvb.tif")
    rgb = img.read()

    mns = io.open(mns)
    mns = mns.read()
    mnt = io.open(mnt)
    mnt = mnt.read()
    MNH = mns - mnt
    mns = None
    mnt = None

    b = np.zeros((5, rgb.shape[1], rgb.shape[2]))
    b[0] = rgb[0]
    b[1] = rgb[0]
    b[2] = rgb[1]
    b[3] = ir[0]
    b[4] = MNH[0]

    ir = None
    rgb = None
    MNH = None

    with io.open("/foo/" + region + "/img_5b_" + region + ".tif",
                 'w',
                 driver='GTiff',
                 height=b.shape[1],
                 width=b.shape[2],
                 count=b.shape[0],
                 dtype=np.float64,
                 transform=img.transform,
                 crs=img.crs
                 ) as dst:
        dst.write(b)
