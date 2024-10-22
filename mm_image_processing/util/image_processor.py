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
from rasterio.features import shapes
import numpy as np
import cv2
import torch
from rasterio.plot import reshape_as_image
from mm_image_processing.util.models import ResNet18_UNet,SegmentModelWrapper
from tqdm import tqdm 

logging.basicConfig(level=logging.DEBUG)

def processImgFromLocal(imgUrl, app):
    """
    Processes an image from the local file system.

    Args:
        img (str): The path or URL of the image file.

    Returns:
        tuple: A tuple containing the image shape, bounding box, and the processed data array.
               The image shape is a tuple (height, width, channels).
               The bounding box is a tuple (left, bottom, right, top).
               The processed data array is a NumPy array.
    """

    app.logger.debug("Process From Local: " + imgUrl)
    dataset = imageToDataset(imgUrl, app)
    app.logger.debug("Image to dataset complete")
    # Add features if needed
    array = formatData(dataset,app)
    # Bounding box and image.shape are needed to construct the geojson after classifying
    app.logger.debug("Format Data complete")

    bbox = dataset.rio.bounds()

    app.logger.debug("Reshaping Image before Returning")
    img = reshape_as_image(dataset.to_array().to_numpy()) 
    # For getting img.shape for geojson
    return img.shape, bbox, array

# loads img from path imgUrl and returns a corrosponding dataset
def imageToDataset(imgUrl:str, app):
    # load data into inputArray then convert it into a dataset for img processing
    app.logger.debug("Image to Dataset")
    # Load data into inputArray then convert it into a dataset for image processing
    inputArray = rioxarray.open_rasterio(imgUrl, chunks=True)
    inputDataSet = inputArray.to_dataset(dim='band')
  
    return inputDataSet

def formatData(dataset, app):
    app.logger.debug("Reshaping Image for Formatting")
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
    
    #output_img = reshape_as_raster(classified_output.reshape(img_shape[0], img_shape[1], 1)) 
    
    transform = rasterio.transform.from_bounds(*bbox, width= classified_output.shape[1], height= classified_output.shape[0])
    
    labels = raster_to_gdf(classified_output, transform, crs = "EPSG:4326", app_logger_warning = app_logger_warning)

    # returning GeoJSON
    return labels

def prediction(image):


    model = ResNet18_UNet(input_image_size=256)
    model.load_state_dict(torch.load('mm_image_processing/util/ResNet18_UNet_epoch_20.pth', map_location='cpu'))
    wrapper = SegmentModelWrapper(model)
    wrapper.eval()

    # Initialize the segmented image with zeros
    segm_img = np.zeros(image.shape[:2])
    weights_sum = np.zeros(image.shape[:2])  # Initialize weights for normalization
    patch_num = 1
    
    
    patch_size = 256



    # Iterate over the image in steps of patch_size
    for i in tqdm(range(0, image.shape[0] - patch_size + 1, patch_size)):   
        for j in range(0, image.shape[1] - patch_size + 1, patch_size): 
            # Extract the patch, ensuring we handle the boundaries
            single_patch = image[i:i+patch_size, j:j+patch_size]
            single_patch_input = np.expand_dims(single_patch, 0) 
            single_patch_input = np.transpose(single_patch_input, (0, 3, 1, 2))

            # Predict and apply Sigmoid
            with torch.no_grad():
                single_patch_input_tensor = torch.from_numpy(single_patch_input).float()
                
                output = wrapper(single_patch_input)
    
                
                binary_mask_np = output.squeeze().cpu().detach().numpy()
    
                
            # Resize the prediction to match the patch size
            single_patch_prediction_resized = cv2.resize(binary_mask_np, (patch_size, patch_size))
            
            # Add the prediction to the segmented image and update weights for normalization
            segm_img[i:i+patch_size, j:j+patch_size] += single_patch_prediction_resized
            weights_sum[i:i+patch_size, j:j+patch_size] += 1
            
            patch_num += 1
            
            

    # Normalize the final segmented image to handle overlaps
    segm_img = np.divide(segm_img, weights_sum, where=weights_sum > 0)

    return segm_img