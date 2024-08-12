"""
Image processing module for preprocessing data to prepare them for classification models

Consists of the following useful functions
    - processImgFromLocal : process image from local directory
    - buildGeoJson : convert classified data to geojson
"""
import logging

import rioxarray
import rasterio
import geopandas as gpd
from rioxarray.merge import merge_datasets
from rasterio.features import shapes
from matplotlib.collections import PatchCollection
import numpy as np
import pandas as pd
import cv2
import torch
import torch.nn as nn
import matplotlib.pyplot as plt
from torchvision import transforms
from rasterio.plot import show
from rasterio.plot import reshape_as_image


from mm_image_processing.util.models import ResNet18_UNet
from PIL import Image
from tqdm import tqdm 






def processImgFromLocal(imgUrl, app):



    app.logger.debug("Process From Local")
    dataset = imageToDataset(imgUrl, app)
    app.logger.debug("Image to dataset complete")
    # Add features if needed
    array = formatData(dataset,app)
    # Bounding box and image.shape are needed to construct the geojson after classifying
    app.logger.debug("Format Data complete")

    bbox = dataset.rio.bounds()
    img = reshape_as_image(dataset.to_array().to_numpy()) 
    # For getting img.shape for geojson
    return img.shape, bbox, array

def imageToDataset(imgUrl: str, app):


    app.logger.debug("Image to Dataser")
    
    # Load data into inputArray then convert it into a dataset for image processing
    inputArray = rioxarray.open_rasterio(imgUrl, chunks=True)
    inputDataSet = inputArray.to_dataset(dim='band')
  
    return inputDataSet

def formatData(dataset,app):
    img = reshape_as_image(dataset.to_array().to_numpy())   

    app.logger.debug("Format data")
    if img.shape[2] == 4:
        img_rgb = img[:, :, :3]
        
    else:
        img_rgb = img
    #array = img_rgb.reshape(img_rgb.shape[0], img_rgb.shape[1], img_rgb.shape[2])
    return img_rgb


def reshape_as_image(array):
    # This function reshapes the array into the shape of the original image
    return np.moveaxis(array, 0, -1)

def normalize(image):
    # Normalize the RGB image to the range [0, 1]
    return image / 255.0 

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
    array_int = array.astype(np.int16)

    
    results = []
    for s, v in shapes(array_int, mask=None, transform=transform):
        if v == label_val:
            results.append({'properties': {'raster_val': v}, 'geometry': s})
    
    
    labels = gpd.GeoDataFrame.from_features(list(results)).simplify(tolerance=tolerance)
    labels.crs = crs
    
    return labels

      
        
def reshape_as_raster(array):
    """
    Reshape the classified output array into a format suitable for raster processing.
    
    Args:
        array (np.array): The classified output as a NumPy array.
    
    Returns:
        np.array: The reshaped array suitable for raster processing.
    """
    # Assuming the input is a 3D array with shape (height, width, 1)
    if len(array.shape) == 3 and array.shape[2] == 1:
        return array
    else:
        raise ValueError("Input array must have shape (height, width, 1)")
        


def buildGeoJson(img_shape, bbox, classified_output, app_logger_warning=None):
    """
    Builds a GeoJSON using EPSG:32617 from the given inputs.

    Args:
        img_shape (tuple): the shape of the original image
        bbox (tuple): The bounding box related to the classified_output
        classified_output (str): The classified output as a string representation of a NumPy array.
        app_logger_warning (function): A logging function used for debugging.

    Returns:
        dict: The GeoJSON representation of the classified output.
    """
    
  
    total_elements = classified_output.size
 
    

    height, width, _ = img_shape
    expected_elements = height * width

    
    
    output_img = reshape_as_raster(classified_output.reshape(img_shape[0], img_shape[1], 1)) 
    
    transform = rasterio.transform.from_bounds(*bbox, width= output_img.shape[1], height= output_img.shape[0])
    
    labels = raster_to_gdf(classified_output, transform, crs = "EPSG:4326", app_logger_warning = app_logger_warning)

    # returning GeoJSON
    return labels


def prediction(image):


    patch_size = 128
 
    model = ResNet18_UNet()
    model.load_state_dict(torch.load('mm_image_processing/util/imagenet_resnet18_unet.pth', map_location=torch.device('cpu')))
    model.eval()
    model = model.to('cpu')


    segm_img = np.zeros(image.shape[:2])
    weights_sum = np.zeros(image.shape[:2])
    sigmoid = nn.functional.sigmoid
    for i in tqdm(range(0, image.shape[0] - patch_size + 1, patch_size)):
        for j in range(0, image.shape[1] - patch_size + 1, patch_size):
            single_patch = image[i:i+patch_size, j:j+patch_size]
            single_patch_norm = normalize(single_patch)
            single_patch_input = np.expand_dims(single_patch_norm, 0)
            single_patch_input = np.transpose(single_patch_input, (0, 3, 1, 2))
            with torch.no_grad():
                single_patch_input_tensor = torch.from_numpy(single_patch_input).float()
                output = model(single_patch_input_tensor.to('cpu'))
                threshold = 10**(-10)
                probabilities = sigmoid(output)
                binary_mask = (probabilities > threshold).int()
                binary_mask_np = binary_mask.squeeze().cpu().detach().numpy()
            single_patch_prediction_resized = cv2.resize(binary_mask_np, (patch_size, patch_size))
            segm_img[i:i+patch_size, j:j+patch_size] += single_patch_prediction_resized
            weights_sum[i:i+patch_size, j:j+patch_size] += 1
    segm_img = np.divide(segm_img, weights_sum, where=weights_sum > 0)
    return segm_img