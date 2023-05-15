from rasterio.plot import reshape_as_image, reshape_as_raster
import rasterio
import rioxarray
from util import features
from rasterio.features import shapes
import geopandas as gpd
import numpy as np

import logging

logging.basicConfig(level=logging.DEBUG)


# returns a processed npArray
def processImgFromS3(img_ref):
    # TODO fill in method
    raise NotImplementedError


# returns a processed npArray
def processImgFromLocal(img):
    dataset = imageToDataset(img)
    addFeatures(dataset=dataset)
    array = formatData(dataset)
    bbox = dataset.rio.bounds()
    img = reshape_as_image(dataset.to_array().to_numpy()) # for getting img.shape for geojson

    return img.shape, bbox, array


def imageToDataset(imgUrl:str):
    inputArray = rioxarray.open_rasterio(imgUrl,chunks=True)
    # img_shape = inputArray.shape
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

def raster_file_to_gdf(fname, tolerance = 0.00005, label_val = 1,  crs = "EPSG:4326"):
     with rasterio.Env():
        with rasterio.open(fname) as src:
            image = src.read(1) # first band
            results = (
                {'properties': {'raster_val': v}, 'geometry': s}
                for i, (s, v) 
                in enumerate(
                    shapes(image, mask = None, transform = src.transform)) if v == label_val)

            df = gpd.GeoDataFrame.from_features(list(results)).simplify(tolerance = tolerance)
            df.crs = crs
            
            return df
        
def raster_to_gdf(array, transform, tolerance = 0.00005, label_val = 1,  crs = "EPSG:4326", app_logger_warning=print):
    results = ({'properties': {'raster_val': v}, 'geometry': s} for i, (s, v) in enumerate(shapes(array.astype(np.int16), mask = None, transform = transform)) if v == label_val)
    # app_logger_warning("APP_LOGGER_WARNING SUCESS")
    labels = gpd.GeoDataFrame.from_features(list(results)).simplify(tolerance = tolerance)
    labels.crs = crs

    return  labels

# TODO fix this using https://corteva.github.io/rioxarray/stable/examples/transform_bounds.html as example
def buildGeoJson(img_shape, bbox, classified_output, app_logger_warning):
    app_logger_warning(f'BBOX:{bbox}')

    # output_img = reshape_as_raster(classified_output.reshape(img_shape[0], img_shape[1], img_shape[2])) #works but fails on transform.from_bounds
    classified_output = np.array(eval(classified_output))  # Convert the string to a numpy array

    output_img = reshape_as_raster(classified_output.reshape(img_shape[0], img_shape[1], 1)) 
    transform = rasterio.transform.from_bounds(*bbox, width= output_img.shape[2], height= output_img.shape[1])
    labels = raster_to_gdf(output_img, transform, crs = "EPSG:32617", app_logger_warning = app_logger_warning)

    # Saving GeoJSON
    return labels