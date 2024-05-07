#!/usr/bin/python3

import json
import socket
from flask import Flask, app
import openeo
from flask_sock import Sock
import numpy as np
import asyncio
import rasterio
from openeo.processes import ProcessBuilder


# First, we connect to the back-end and authenticate.
con = openeo.connect("openeo.dataspace.copernicus.eu")
con.authenticate_oidc()


def scale_function(x: ProcessBuilder):
    return x.linear_scale_range(0, 6000, 0, 255)


def get_satelite_image_nir(
    south=23.81,
    west=-77.54,
    north=23.86,
    east=-77.53,
    start_date="2024-04-01",
    end_date="2024-04-16",
    filename="temp.tiff",
):
    toload = ["B08"]

    datacube = con.load_collection(
        "SENTINEL2_L2A",
        spatial_extent={
            "south": south,
            "west": west,
            "north": north,
            "east": east,
        },
        temporal_extent=[start_date, end_date],
        bands=toload,
    )

    datacube = datacube.mean_time()

    datacube = datacube * 0.0001

    datacube.download(filename, format="GTiff")

    # cube_nir = datacube.filter_bands(bands=["B08"])

    # cube_nir = cube_nir * 0.0001

    # cube_nir = cube_nir.max_time()

    # cube_nir.download(filename, format="GTiff")

    return None


def calculate_cloud_coverage_nir(geotiff_path, threshold):
    # Open the GeoTIFF file
    with rasterio.open(geotiff_path) as src:
        # Read the first band (assuming it's a single-band, grayscale image)
        band1 = src.read(1)

        # Apply a threshold to classify pixels as cloud/non-cloud
        # Assuming higher values are clouds
        cloud_pixels = band1 > threshold

        # Calculate the percentage of cloud pixels
        cloud_coverage = np.sum(cloud_pixels) / cloud_pixels.size * 100

        return cloud_coverage


def calculate_cloud_coverage_rgb(geotiff_path, threshold):
    with rasterio.open(geotiff_path) as src:
        # Read the first band (assuming it's a single-band, grayscale image)
        b = src.read(1)
        g = src.read(2)
        r = src.read(3)
        avg = (b + g + r) / 3

        # Apply a threshold to classify pixels as cloud/non-cloud
        # Assuming higher values are clouds
        cloud_pixels = avg > threshold

        # Calculate the percentage of cloud pixels
        cloud_coverage = np.sum(cloud_pixels) / cloud_pixels.size * 100

        return cloud_coverage


def read_geotiff_values(geotiff_path):
    # Open the GeoTIFF file
    with rasterio.open(geotiff_path) as src:
        # Read all bands
        b = src.read(1)
        g = src.read(2)
        r = src.read(3)

        avg = (b + g + r) / 3

        print(avg)


def get_satelite_image_rgb(
    south=23.81,
    west=-77.54,
    north=23.86,
    east=-77.53,
    start_date="2024-04-01",
    end_date="2024-04-16",
    filename="temp.tiff",
):
    # Now that we are connected, we can initialize our datacube object with the area of interest
    # and the time range of interest using Sentinel 1 data.

    toload = ["B02", "B03", "B04", "SCL"]

    datacube = con.load_collection(
        "SENTINEL2_L2A",
        spatial_extent={
            "south": south,
            "west": west,
            "north": north,
            "east": east,
        },
        temporal_extent=[start_date, end_date],
        bands=toload,
    )

    datacube = datacube.mean_time()
    datacube = datacube * 0.0001
    datacube.download(filename, format="GTiff")

    return None


if __name__ == "__main__":
    # get_satelite_image_nir(
    #     north=32.88424, west=-117.23666, south=32.88058, east=-117.23249
    # )
    get_satelite_image_rgb()
    read_geotiff_values("temp.tiff")
    print(calculate_cloud_coverage_rgb("temp.tiff", 0.5))

    # app.run(debug=False, port=5001, host="0.0.0.0")
