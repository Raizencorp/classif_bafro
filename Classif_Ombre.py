import rasterio as io
import numpy as np
from skimage import measure
from tqdm import tqdm
import pickle
from post_pro import post_pro

def classif_Ombre(region, model):
    ########## Path ########
    poly =          "/foo/" + region + "/GradBoost_" + region + "_model_5R.tif"

    rgb =           "/foo/" + region + "/D032_2019_" + region + "_b100_rvb.tif"
    ir =            "/foo/" + region + "/D032_2019_" + region + "_b100_irc.tif"

    path_out =      "/foo/" + region + "/GradBoost_" + region + "_4R_2C_ir_NDVI.tif"
    path_model =    model

    poly = io.open(poly)
    poly = poly.read()
    poly = poly[0, :, :].astype(np.int32)

    img = io.open(rgb)
    rgb = img.read()

    ir = io.open(ir)
    ir = ir.read()

    NDVI = (ir[0].astype(float) - rgb[0].astype(float)) / (rgb[0].astype(float) + ir[0].astype(float))
    NDVI = np.around(NDVI, decimals=3)

    band = np.empty((2, rgb.shape[1], rgb.shape[2]))
    band[0] = ir[0]
    band[1] = NDVI
    ir = None
    NDVI = None

    ############## COORDONNEE OMBRE ################
    mesures = measure.regionprops(poly)
    poly = None
    coordinates = []
    for i in range(4):
        coordinates.append(mesures[i].coords.swapaxes(0, -1))
    ombre = coordinates[3]
    coordinates = None

    ############# Data ################
    print("Preparing Data for Predict")
    data = np.empty((len(ombre[0]), band.shape[0]))
    value = []
    for i in range(band.shape[0]):
        for j in tqdm(range(len(ombre[0]))):
            value.append(band[i][ombre[0][j]][ombre[1][j]])
        data[:, i] = value
        value = []

    ############## Predict ###############
    print("Predicting")
    model = pickle.load(open(path_model, 'rb'))
    predict = model.predict(data)

    ############## Out ###############
    print("Creating file")
    out = np.empty((1, rgb.shape[1], rgb.shape[2]))
    out[::] = -1
    for j in tqdm(range(len(ombre[0]))):
        out[0][ombre[0][j]][ombre[1][j]] = predict[j]

    print("Writing file")
    with io.open(path_out,
                 'w',
                 driver='GTiff',
                 height=out.shape[1],
                 width=out.shape[2],
                 count=1,
                 dtype=out.dtype,
                 transform=img.transform,
                 crs=img.crs) as dst:
        dst.write(out)

    ############ Post Pro #################
    print("Post process")
    post_pro(path_out)
