from rasterio.plot import reshape_as_image
import rasterio
import rioxarray
from util import features
from rasterio.features import shapes
# import geopandas as gpd


# returns a processed npArray
def processImgFromS3(img_ref):
    # TODO fill in method
    raise NotImplementedError


# returns a processed npArray
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
        
def raster_to_gdf(array, transform, tolerance = 0.00005, label_val = 1,  crs = "EPSG:4326"):
    results = ({'properties': {'raster_val': v}, 'geometry': s} for i, (s, v) in enumerate(shapes(array.astype(np.int16), mask = None, transform = transform)) if v == label_val)
    labels = gpd.GeoDataFrame.from_features(list(results)).simplify(tolerance = tolerance)
    labels.crs = crs

    return  labels

# TODO fix this using https://corteva.github.io/rioxarray/stable/examples/transform_bounds.html as example
def buildGeoJson(output_img):
    transform = rasterio.transform.from_bounds(*bbox, width= output_img.shape[2], height= output_img.shape[1])
    labels = raster_to_gdf(output_img, transform, crs = "EPSG:32617")

    # Saving GeoJSON
    labels.to_file('labels.geojson', driver='GeoJSON')  
    return labels