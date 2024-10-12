import gdal
import numpy as np
import skimage.morphology

def tif2array(tif):
    DS=gdal.Open(tif)
    array=np.zeros((DS.RasterYSize,DS.RasterXSize,DS.RasterCount),DS.GetRasterBand(1).ReadAsArray().dtype)
    for bande in range(DS.RasterCount):
        array[:,:,bande]=DS.GetRasterBand(bande+1).ReadAsArray()
    return array, DS.GetGeoTransform(),DS.GetProjection()

def array2tif(array,path,proj,trans,bands):
    dim = [array.shape[1], array.shape[0]]
    driver = gdal.GetDriverByName("GTiff")
    co = ['COMPRESS=DEFLATE', 'NUM_THREADS=ALL_CPUS', "BIGTIFF=YES"]
    gdt = gdal.GDT_Int16

    outRaster = gdal.GetDriverByName("GTiff").Create(path, dim[0], dim[1],bands , gdt, options=co)
    for i in range(bands):
        outband = outRaster.GetRasterBand(i + 1).WriteArray(array)
        print('saved')
    outRaster.SetGeoTransform(trans)
    outRaster.SetProjection(proj)
    return


def post_pro(path):
    img,trans,proj=tif2array(path)
    IMG=img[:,:,0]
    ball3=skimage.morphology.disk(3)
    ball2=skimage.morphology.disk(2)
    #SEPARATION
    REMOVED_FROM_VEGE=np.copy(IMG).astype(np.bool)*0
    REMOVED_FROM_IMPER=np.copy(IMG).astype(np.bool)*0

    OMBRES=np.copy(IMG).astype(np.bool)*0
    OMBRES[np.nonzero(IMG==-1)]=0
    OMBRES[np.nonzero(IMG!=-1)]=1

    NEGA_OMBRES=np.copy(IMG).astype(np.bool)*0
    NEGA_OMBRES[np.nonzero(IMG==-1)]=1

    VEGE=np.copy(IMG).astype(np.bool)*0
    VEGE[np.nonzero(IMG==1)]=1

    IMPER=np.copy(IMG).astype(np.bool)*0
    IMPER[np.nonzero(IMG==2)]=1

    #TRAITEMENT
    VEGE_PROCESSED=skimage.morphology.remove_small_objects(VEGE.astype(np.bool),20,connectivity=1,in_place=True)

    REMOVED_FROM_VEGE=REMOVED_FROM_VEGE+VEGE-VEGE_PROCESSED

    IMPER=skimage.morphology.dilation(IMPER.astype(np.bool),ball3)*OMBRES #Extention de l'ombre non-vege et recoupe par mask d'ombre global
    IMPER=skimage.morphology.remove_small_holes(IMPER.astype(np.bool),5)*OMBRES # élimination des petits éléments végé créés par la dernière opération
    IMPER=(np.where(IMPER-skimage.morphology.dilation(np.where(IMPER+NEGA_OMBRES==0,1,0).astype(np.bool),ball2)*OMBRES<=0,0,1)*OMBRES).astype(np.bool) #petite diminution du mask non-végé

    REMOVED_FROM_VEGE=REMOVED_FROM_VEGE+VEGE-VEGE_PROCESSED

    IMPER_REMOVED=np.where(skimage.morphology.remove_small_holes(np.where(IMPER==1,0,1).astype(np.bool),30,connectivity=1)==1,0,1).astype(np.bool)

    REMOVED_FROM_IMPER=IMPER.astype(np.int8)-IMPER_REMOVED.astype(np.int8)




    #RECOMPOSITION
    IMG=IMG.astype(np.int8)*0
    IMG[np.nonzero(VEGE_PROCESSED)]=1
    IMG[np.nonzero(IMPER)]=2
    IMG[np.nonzero(REMOVED_FROM_IMPER)]=1
    IMG[np.nonzero(REMOVED_FROM_VEGE)]=2
    IMG[np.nonzero(OMBRES==0)]=0

    array2tif(IMG,path,proj,trans,1)

