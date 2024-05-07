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
    toload = []

    toload = ["B02", "B03", "B04", "B08"]

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

    cube_r = datacube.filter_bands(bands=["B04"])
    cube_g = datacube.filter_bands(bands=["B03"])
    cube_b = datacube.filter_bands(bands=["B02"])
    cube_nir = datacube.filter_bands(bands=["B08"])

    datacube_a = datacube * 0.1
    datacube_b = datacube * 0.2
    datacube_c = datacube * 0.3
    datacube_d = datacube * 0.05
    datacube_e = datacube * 0.025
    datacube_f = datacube * 0.075

    datacube_a = datacube_a.mean_time()
    datacube_b = datacube_b.mean_time()
    datacube_c = datacube_c.mean_time()
    datacube_d = datacube_d.mean_time()
    datacube_e = datacube_e.mean_time()
    datacube_f = datacube_f.mean_time()

    # datacube = datacube.linear_scale_range(0, 0.3, 0, 255)

    cube_r = cube_r * 0.0001
    cube_g = cube_g * 0.0001
    cube_b = cube_b * 0.0001
    cube_nir = cube_nir * 0.0001

    # mean_time() is a shortcut function
    cube_r = cube_r.mean_time()
    cube_g = cube_g.mean_time()
    cube_b = cube_b.mean_time()

    res = datacube_a.save_result(
        format="GTiff",
        options={
            "red": "B04",
            "green": "B03",
            "blue": "B02",
        },
    )

    res.download("rgb_0_1.tiff", format="GTiff")

    # res = cube_s2_b8.save_result(
    #     format="PNG", options={"red": "B08", "green": "B08", "blue": "B08"}
    # )

    # # send job to back-end
    # job = res.create_job(title="NIR_as_PNG_py2")

    # cube_r.download("red.tiff", format="GTiff")
    # cube_g.download("green.tiff", format="GTiff")
    # cube_b.download("blue.tiff", format="GTiff")

    # cube_nir.download("nir.tiff", format="GTiff")
    # res_nir = cube_nir.save_result(
    #     format="PNG", options={"red": "B08", "green": "B08", "blue": "B08"}
    # )
    # res_nir.download("nir.png", format="PNG")

    # datacube = datacube.mean_time()

    # res = datacube.save_result(
    #     format="PNG",
    #     options={
    #         "red": "B04",
    #         "green": "B03",
    #         "blue": "B02",
    #     },
    # )

    # job = res.create_job(title="temporal_mean_as_PNG")

    # features = ["blue", "green", "red", "nir", "swir", "ndvi", "ndwi", "mi"]
    # arrs = []
    # for feature in features:
    #     with rasterio.open(f"{feature}.tiff") as src:
    #         data = src.read()
    #         print(data)
    #         arrs.append(data)

    # toRet = np.array(arrs)

    # convert from openeo datacube to numpy array

    # blue = np.array(blue, dtype=np.float64)
    # green = np.array(green)
    # red = np.array(red)
    # nir = np.array(nir)
    # swir = np.array(swir)

    # ndvi = np.divide(nir - red, nir + red, where=(nir + red != 0), dtype=np.float64)

    # ndwi = np.divide(
    #     green - nir, green + nir, where=(green + nir != 0), dtype=np.float64
    # )

    # mi = np.divide(nir - swir, nir + swir, where=(nir + swir != 0), dtype=np.float64)

    return None


if __name__ == "__main__":
    get_satelite_image_rgb(
        north=32.88424, west=-117.23666, south=32.88058, east=-117.23249
    )
    # app.run(debug=False, port=5001, host="0.0.0.0")
