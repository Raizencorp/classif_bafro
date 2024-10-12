import rasterio as io
import numpy as np
from skimage import measure
from tqdm import tqdm

def fuse(region, mode):
    ########## Path ########
    seg =           "/foo/" + region + "/Seg_5b_" + region + "_125.tif"
    poly_path =     "/foo/" + region + "/GradBoost_" + region + "_5R.tif"
    poly_ombre =    "/foo/" + region + "/GradBoost_" + region + "_4R_2C_ir_NDVI.tif"

    path_out =      "/foo/" + region + "/Fuse_" + region + "_PI.tif"

    img = io.open(poly_path)
    poly = img.read()
    poly = poly[0, :, :].astype(np.int32)
    mesures = measure.regionprops(poly)
    poly = None
    coordinates = []
    for i in range(4):
        coordinates.append(mesures[i].coords.swapaxes(0, -1))
    ombre = coordinates[3]
    coordinates = []

    poly_ombre = io.open(poly_ombre)
    poly_ombre = poly_ombre.read()
    poly_ombre = poly_ombre[0, :, :].astype(np.int32)
    mesures = measure.regionprops(poly_ombre)
    for i in range(2):
        coordinates.append(mesures[i].coords.swapaxes(0, -1))
    vege = coordinates[0]
    route = coordinates[1]
    coordinates = None

    if mode == 1:
        perm = np.zeros((poly_ombre.shape[0], poly_ombre.shape[1]))
        for i in tqdm(range(len(vege[0]))):
            perm[vege[0][i]][vege[1][i]] = 1

        imperm = np.zeros((poly_ombre.shape[0], poly_ombre.shape[1]))
        for i in tqdm(range(len(route[0]))):
            imperm[route[0][i]][route[1][i]] = 1

        perm, perm_size = measure.label(perm, connectivity=2, return_num=True)
        imperm, imperm_size = measure.label(imperm, connectivity=2, return_num=True)

        seg = io.open(seg)
        seg = seg.read()
        seg = seg[0, :, :].astype(np.int32)
        mesures = measure.regionprops(seg)
        size = len(mesures)

        for i in tqdm(range(1, len(route[0]))):
            seg[route[0][i]][route[1][i]] = imperm[route[0][i]][route[1][i]] + size

        for i in tqdm(range(1, len(vege[0]))):
            seg[vege[0][i]][vege[1][i]] = perm[vege[0][i]][vege[1][i]] + size + imperm_size

        out = np.empty((1, seg.shape[0], seg.shape[1]))
        out[0] = seg

    elif mode == 2:
        poly = io.open(poly_path)
        poly = poly.read()
        poly = poly[0, :, :].astype(np.int32)

        poly_ombre = np.where(poly_ombre == 2, 4, poly_ombre)
        poly_ombre = np.where(poly_ombre == 1, 4, poly_ombre)

        for i in tqdm(range(len(ombre[0]))):
            poly[ombre[0][i]][ombre[1][i]] = poly_ombre[ombre[0][i]][ombre[1][i]]

        poly = np.where(poly == 2, 11, poly)
        poly = np.where(poly == 3, 2, poly)
        poly = np.where(poly == 1, 4, poly)
        poly = np.where(poly == 0, 1, poly)
        poly = np.where(poly == 4, 0, poly)

        out = np.empty((1, poly.shape[0], poly.shape[1]))
        out[0] = poly
    else:
        poly = io.open(poly_path)
        poly = poly.read()
        poly = poly[0, :, :].astype(np.int32)

        poly_ombre = np.where(poly_ombre == 2, 4, poly_ombre)
        poly_ombre = np.where(poly_ombre == 1, 5, poly_ombre)

        for i in tqdm(range(len(ombre[0]))):
            poly[ombre[0][i]][ombre[1][i]] = poly_ombre[ombre[0][i]][ombre[1][i]]

        out = np.empty((1, poly.shape[0], poly.shape[1]))
        out[0] = poly
        path_out = "/foo/" + region + "/Fuse_" + region + "_dev.tif"

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
