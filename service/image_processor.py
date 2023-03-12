from rasterio.plot import reshape_as_image
import rioxarray
import service.features

def processImgFromLocal(img):
    dataset = imageToDataset(img)
    addFeatures(dataset=dataset)
    array = formatData(dataset)
    return array


def imageToDataset(imgUrl:str):
    inputArray = rioxarray.open_rasterio(imgUrl,chunks=True)
    inputDataSet = inputArray.to_dataset(dim='band')
    return inputDataSet


def addFeatures(dataset):
    dataset['ndvi'] = features.s2_ndvi(dataset)
    dataset['nvwi'] = features.s2_ndwi(dataset)
    dataset['water_dist'] = features.s2_distance_to_water(dataset, threshold = 0)
    return dataset

def formatData(dataset):
    img = reshape_as_image(dataset.to_array().to_numpy())
    # This array can then be sent over, in chunks to the classification service
    array = img.reshape(img.shape[0] * img.shape[1], img.shape[2])
    return array