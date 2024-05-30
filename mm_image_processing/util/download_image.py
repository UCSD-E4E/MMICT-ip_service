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
from datetime import datetime, timedelta
import time
import os


# First, we connect to the back-end and authenticate.
con = openeo.connect("openeo.dataspace.copernicus.eu")
con.authenticate_oidc()


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


def calculate_cloud_coverage_nir(geotiff_path, threshold):
    with rasterio.open(geotiff_path) as src:
        # Read the first band (assuming it's a single-band, grayscale image)
        band1 = src.read(1)

        # Apply a threshold to classify pixels as cloud/non-cloud
        # Assuming higher values are clouds
        cloud_pixels = band1 > threshold

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


def read_nir_geotiff_values(geotiff_path):
    with rasterio.open(geotiff_path) as src:
        # Read the first band (assuming it's a single-band, grayscale image)
        band1 = src.read(1)

        print(band1)


def get_date_list(start_date_str, end_date_str):
    start_date = datetime.strptime(start_date_str, "%Y-%m-%d")

    end_date = datetime.strptime(end_date_str, "%Y-%m-%d")

    # Initialize an empty list to hold the date strings
    date_list = []

    # Iterate over the date range and generate the list of date strings
    current_date = start_date
    while current_date <= end_date:
        # Append the current date as a string in the desired format
        date_list.append(current_date.strftime("%Y-%m-%d"))
        # Move to the next date
        current_date += timedelta(days=1)

    return date_list


def get_single_satelite_image_nir(
    south=23.81,
    west=-77.54,
    north=23.86,
    east=-77.53,
    target_date="2024-04-10",
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
        temporal_extent=[target_date, target_date],
        bands=toload,
    )

    datacube = datacube.mean_time()
    datacube = datacube * 0.0001

    try:
        datacube.download(filename, format="GTiff")
        print("Image downloaded for date: {d}".format(d=target_date))
    except Exception as e:
        print("No image found for date: {d}".format(d=target_date))
        return False

    return True


def find_min_cloud_image_nir(dates, swne, threshold, valid_dates):
    min_cloud_image = None
    min_cloud_coverage = 100
    dir_name = swne + str(threshold)

    for d in dates:
        if valid_dates[d]:
            cloud_coverage = calculate_cloud_coverage_nir(
                "{swne}_{d}.tiff".format(d=d, swne=swne), threshold
            )
            if cloud_coverage < min_cloud_coverage:
                min_cloud_coverage = cloud_coverage
                min_cloud_image = "{swne}_{d}.tiff".format(d=d, swne=swne)
            mask_image_nir(
                "{swne}_{d}.tiff".format(d=d, swne=swne),
                "{swne}_{d}_{thresh}_bw.tiff".format(d=d, swne=swne, thresh=threshold),
                threshold,
            )

            os.rename(
                "{swne}_{d}.tiff".format(d=d, swne=swne),
                "{dir_name}/{d}.tiff".format(d=d, dir_name=dir_name),
            )
            os.rename(
                "{swne}_{d}_{thresh}_bw.tiff".format(d=d, swne=swne, thresh=threshold),
                "{dir_name}/{d}_{thresh}_bw.tiff".format(
                    d=d, dir_name=dir_name, thresh=threshold
                ),
            )

    return min_cloud_image


def get_min_satelite_images_nir(
    south=23.81,
    west=-77.54,
    north=23.86,
    east=-77.53,
    target_date="2024-04-10",
    threshold=0.5,
):
    toload = ["B08"]

    # 2 weeks before target date
    start_date = datetime.strptime(target_date, "%Y-%m-%d") - timedelta(days=14)
    start_date = start_date.strftime("%Y-%m-%d")

    # 2 weeks after target date
    end_date = datetime.strptime(target_date, "%Y-%m-%d") + timedelta(days=14)
    end_date = end_date.strftime("%Y-%m-%d")

    dates = get_date_list(start_date, end_date)
    valid_dates = {}

    swne = "{s}_{w}_{n}_{e}".format(s=south, w=west, n=north, e=east)
    dir_name = swne + str(threshold)
    os.mkdir(dir_name)
    for d in dates:
        time.sleep(5)
        valid_dates[d] = get_single_satelite_image_nir(
            south=south,
            west=west,
            north=north,
            east=east,
            target_date=d,
            filename="{swne}_{d}.tiff".format(d=d, swne=swne),
        )

    min_cloud_image = find_min_cloud_image_nir(dates, swne, threshold, valid_dates)
    return min_cloud_image


def mask_image_nir(geotiff_path, target_path, threshold):
    with rasterio.open(geotiff_path) as src:
        # Read the first band (assuming it's a single-band, grayscale image)
        band1 = src.read(1)

        # Apply a threshold to classify pixels as cloud/non-cloud
        # Assuming higher values are clouds
        cloud_pixels = band1 > threshold

        # below threshold is 0, above threshold is 1
        masked_image = cloud_pixels.astype(np.uint8)

        # Write the masked image to a new GeoTIFF file
        with rasterio.open(target_path, "w", **src.profile) as dst:
            dst.write(masked_image, 1)

        return masked_image


def mask_already_downloaded(swne, threshold):
    # check every image in the directory
    for filename in os.listdir(swne):
        print(filename)
        wo_tiff = filename.split(".")[0]
        # if filename contains "bw" then it is already masked
        if "bw" in filename:
            continue
        mask_image_nir(
            filename,
            "{swne}/{wo_tiff}_{thresh}_bw.tiff".format(
                wo_tiff=wo_tiff, swne=swne, thresh=round(threshold, 3)
            ),
            threshold,
        )


def get_satelite_image_rgb(
    south=23.81,
    west=-77.54,
    north=23.86,
    east=-77.53,
    start_date="2024-04-10",
    end_date="2024-04-11",
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
    try:
        datacube.download(filename, format="GTiff")
    except Exception as e:
        print(e)
        return False

    return None


if __name__ == "__main__":
    # get_satelite_image_nir(
    #     north=32.88424, west=-117.23666, south=32.88058, east=-117.23249
    # )
    for i in range(0, 10):
        mask_already_downloaded("17.8_-77.0_17.9_-76.90.7", i * 0.1)

    # read_nir_geotiff_values("2024-04-11.tiff")
    # print(calculate_cloud_coverage_nir("2024-04-11.tiff", 0.2))
    # mask_image_nir("2024-04-11.tiff", "2024-04-11_bw.tiff", 0.2)
    # app.run(debug=False, port=5001, host="0.0.0.0")
