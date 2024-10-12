import rasterio as io
import numpy as np
import pickle
from tqdm import tqdm
from joblib import Parallel, delayed
from skimage import measure

def classif_BAFRO(region, model):
    ############# SEGMENTATION + RASTER Path ###############
    poly =          "/foo/" + region + "/Seg_5b_" + region + "_125.tif"
    rgb =           "/foo/" + region + "/D032_2019_" + region + "_b100_rvb.tif"
    ir =            "/foo/" + region + "/D032_2019_" + region + "_b100_irc.tif"
    mns =           "/foo/" + region + "/mns.tif"
    mnt =           "/foo/" + region + "/D032_2019_" + region + "_b100_mnt.tif"
    laplace =       "/foo/" + region + "/laplacev2_" + region + ".tif"

    ################## SAVE CONFIG ####################
    path_model =        model
    path_raster =       "/foo/" + region + "/GradBoost_" + region + "_5R.tif"

    ############# SEGMENTATION + RASTER Load ###############

    poly = io.open(poly)
    poly = poly.read()
    poly = poly[0, :, :].astype(np.int32)

    img = io.open(rgb)
    rgb = img.read()
    r = rgb[0:1]

    ir = io.open(ir)
    ir = ir.read()
    ir = ir[0:1]

    mns = io.open(mns)
    mns = mns.read()

    mnt = io.open(mnt)
    mnt = mnt.read()

    laplace = io.open(laplace)
    laplace = laplace.read()

    mesures = measure.regionprops(poly)
    size = len(mesures)

    ################## Calculate Band ####################
    NDVI = (ir.astype(float) - r.astype(float)) / (r.astype(float) + ir.astype(float))
    NDVI = np.around(NDVI, decimals=3)
    MNH = mns - mnt
    mns = None
    mnt = None

    ################## Parallelisation lecture polygone #######################
    def feature(RGB, LP, coordinate):
        tab = np.zeros(9)
        tab[0] = np.mean(RGB[0])
        tab[1] = np.mean(RGB[1])
        tab[2] = np.mean(RGB[2])
        tab[3] = np.mean(LP[0])
        tab[4] = np.mean(LP[1])
        tab[5] = np.mean(LP[2])
        tab[6] = np.mean(MNH[:, coordinate[0], coordinate[1]])
        tab[7] = np.mean(NDVI[:, coordinate[0], coordinate[1]])
        tab[8] = np.mean(ir[:, coordinate[0], coordinate[1]])

        return tab

    id_coordinates = []
    for i in tqdm(range(size)):
        id_coordinates.append(mesures[i].coords.swapaxes(0, -1))

    data = np.array(Parallel(n_jobs=-1)(delayed(feature)(
        rgb[:, id_coordinates[k][0], id_coordinates[k][1]],
        laplace[:, id_coordinates[k][0], id_coordinates[k][1]],
        id_coordinates[k]) for k in tqdm(range(0, size))))
    
    data = np.array(data)

    ################## Predict ###################
    model = pickle.load(open(path_model, 'rb'))
    predict = model.predict(data)

    ################## Write ###############
    result = np.zeros((1, rgb.shape[1], rgb.shape[2]))

    for i in range(size):
        result[:, id_coordinates[i][0], id_coordinates[i][1]] = predict[i]
    
    with io.open(path_raster,
                 'w',
                 driver='GTiff',
                 height=result.shape[1],
                 width=result.shape[2],
                 count=1,
                 dtype=result.dtype,
                 transform=img.transform,
                 crs=img.crs) as dst:
        dst.write(result)

    laplace = None
    mesures = None
    result = None
