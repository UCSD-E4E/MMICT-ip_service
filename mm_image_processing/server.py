"""

"""
import math
import logging
import requests
import random
import string
import json
import asyncio
import websockets
import zlib
import os
import torch

from dotenv import load_dotenv
from threading import Thread, Lock
from flask_sock import Sock
from flask import Flask, request, make_response
from flask_cors import CORS
from flask_csp.csp import csp_header



# Ultility functions from the util directory  
from mm_image_processing.util import image_processor  
from mm_image_processing.util.image_processor import processImgFromLocal, prediction, buildGeoJson
from mm_image_processing.util.s3_img_getter import deleteImg, getImg

logging.basicConfig(level=logging.DEBUG)


logging.getLogger('rasterio').setLevel(logging.WARNING)
load_dotenv()

app = Flask(__name__)
sock = Sock(app)  # create a websocket
CORS(app)  # allow cross origin requests

# IP and port address of the classification service
CLASSIFY_IP = "172.18.0.3" # "container-service"
CLASSIFY_PORT = "5001" 
IMAGE_SERVICE_IP = os.getenv("HOST_IP")
IMAGE_SERVICE_PORT = os.getenv("PORT")

# Configure Flask logging
if not app.debug:
    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)

@app.route("/")
def home():
    return "<h1>Processing Server</h1>"

# for testing websocket connections
@sock.route('/echo')
def ws_echo(ws):
    while (True):
        data = ws.receive()
        ws.send(data)

@sock.route('/ws-process')
def ws_process(ws):
    """
    Route for classifying an image over a WebSocket connection.

    The function performs the following steps while sending progress updates back over the websocket.:
        1. Validates the request data received over the WebSocket connection.
        3. Downloads the image specified in the request from an S3 bucket.
        4. Processes the downloaded image.
        5. Classifies the processed image using a specified classifier.
        6. Builds and returns GeoJSON representation from the classified data.

    """

    app.logger.debug("received request")

    # recieve the websocket data
    data = ws.receive()
    app.logger.debug("validating request: " + data)

    # validate request matches expected json format
    if not validate_process_request_json(data):
        ws.send('invalid request, killing connection')
        ws.close(1)
        return

    # now that it is known to be "safe" load json object, accept the request
    request_json = json.loads(data, strict=False)
    rgb_img_ref = request_json['rgb_image_ref']
    nir_img_ref = request_json['nir_image_ref']
    date_of_capture = request_json['date_of_capture']
    location = request_json['location']
    r_channel = request_json['r_channel']
    g_channel = request_json['g_channel']
    b_channel = request_json['b_channel']
    nir_channel = request_json['nir_channel']

    # write back progress update on the websocket
    progress = {"status": "Accepted classification request", "percent": 5}
    msg = json.dumps(progress)
    ws.send(msg)




    # write back progress again
    progress = {"status": "Downloading specified imagery", "percent": 10}
    msg = json.dumps(progress)
    ws.send(msg)



    # try to download the image at rgb_img_ref and nir_img_ref from the s3 bucket

    # Note: For the dummy-upload branch, the file being downloaded is NOT the one being returned back, this
    # is simply a sanity check to ensure the download is working properly. It may be valuable to keep this 
    # to ensure any production-ready code is playing nicely with S3 as expected.
    try:
        rgbImgUrl = getImg(rgb_img_ref, app)
        #nirImgUrl = getImg(nir_img_ref, app)
    except Exception as e:
        app.logger.error(e)
        ws.close(1)
        return
    

    app.logger.debug("New step!!!!!!!!!!")

   
    # write back progress again
    progress = {"status": "Preparing to preprocess imagery", "percent": 15}
    msg = json.dumps(progress)
    ws.send(msg)

    # Currently, all processing is skipped in the pipeline for the purposes of demoing the GEOJSon transfer between services
    # as the processing has some issues that I'm currently resolving. The architecture between the services is complete, however.
    # -------------------------------------------------------------
    
    # # process the image now that it is downloaded locally


    img_shape, bbox, processed_array = processImgFromLocal(rgbImgUrl, app)


    app.logger.debug("image processing complete")
    app.logger.debug(img_shape)



    progress["status"] = "CLASSIFYING"
    # progress["bbox"] = bbox # write bbox back for debugging purpose only
    # msg = json.dumps(progress)
    # ws.send(msg)

    # # call the classify() method to get classified data from classification_service
    # # * asyncio set so this route does not need to be an async function *
    # asyncio.set_event_loop(asyncio.new_event_loop())
    # classified_array = asyncio.get_event_loop().run_until_complete(
    #     classify(classifier_id, processed_array))  # NOTE use await instead of this since it is cleaner



    classified_array = prediction(processed_array)

    app.logger.debug("prediction complete")



    # # check if classify() method failed
    if classified_array is None:
        ws.send('classification_service error')
        ws.close(1)
        return
    

    # # write back progress update
    progress["status"] = "BUILDING"
    msg = json.dumps(progress)
    ws.send(msg)



    #geojson = json.load(f)
    progress = {"status": "Converting to geojson", "percent": 50}
    msg = json.dumps(progress)
    ws.send(msg)

    # # build geojson from classified data, then convert to a serializable json format
    geojson_raw = buildGeoJson(img_shape, bbox, classified_array)
    app.logger.debug(type(geojson_raw))

    geojson = geojson_raw.to_json()

    app.logger.debug(type(geojson))

    progress = {"status": "Converting to gejson complete", "percent": 50}
    ws.send(msg)

    app.logger.debug("Build Geo Json Complete")


    # try:
    #     f = open('mm_image_processing/labels.json') # working directory is at /ip-service, as defined in the Dockerfile
    # except Exception as e:
    #     app.logger.error(e)
    #     print(os.getcwd())
    #     ws.close(1)
    #     return
    
    # geojson = json.load(f)


    # progress = {"status": "Compressing geodata", "percent": 70}
    # msg = json.dumps(progress)
    # ws.send(msg)

    app.logger.debug("Compressing geojson")

    compressed = zlib.compress(json.dumps(geojson).encode(), 3)

    app.logger.debug("Compressing geojson AFTER" )

    progress = {"status": "Receiving geodata", "percent": 80}
    progress["geojson_flag"] = "sending"    
    msg = json.dumps(progress)
    ws.send(msg)

    geojson_chunks = chunk_geojson(json.dumps(geojson)) # chunk_geojson(str(compressed))
    progress_increment = 20 / len(geojson_chunks)
    for i in range(len(geojson_chunks)):
        progress["geojson_chunk"] = geojson_chunks[i]
        progress["percent"] = round(80 + (i * progress_increment), 2)
        msg = json.dumps(progress)
        ws.send(msg)
    progress["geojson_flag"] = "done"
    progress["status"] = "Completed successfully"
    progress["percent"] = 100
    msg = json.dumps(progress)

    app.logger.debug("Geo Json Send" )   
    # final writeback on websocket, then close connection
    ws.send(msg)
    ws.close()

def chunk_geojson(geojson_str):
    msg = geojson_str
    chunks = []
    chunk_length = 32768 #4096
    for i in range(math.ceil(len(msg) / chunk_length)):
        chunks.append(msg[(chunk_length * i) : (chunk_length * (i + 1))])
    return chunks



def validate_process_request_json(data):
    """
    Validates that the JSON data contains all the required fields. 
    Does NOT validate that it only contains requires fields

    Args:
        data (str): The JSON data to validate.

    Returns:
        bool: True if the JSON data contains all the required fields, False otherwise.
    """

    app.logger.debug("validating request: " + data)
    try:
        request_json = json.loads(data, strict=False)
        if 'rgb_image_ref' not in request_json:
            app.logger.warning("missing rgb_image_ref")
            return False
        if 'nir_image_ref' not in request_json:
            app.logger.warning("missing nir_image_ref")
            return False
        if 'date_of_capture' not in request_json:
            app.logger.warning("missing date_of_capture")
            return False
        if 'location' not in request_json:
            app.logger.warning("missing location")
            return False
        if 'r_channel' not in request_json:
            app.logger.warning("missing r_channel")
            return False
        if 'g_channel' not in request_json:
            app.logger.warning("missing g_channel")
            return False
        if 'b_channel' not in request_json:
            app.logger.warning("missing b_channel")
            return False
        if 'nir_channel' not in request_json:
            app.logger.warning("missing nir_channel")
            return False
        app.logger.debug("Validated request successfully")
        return True
    except Exception as e:
        app.logger.error(e)
        return False


if __name__ == '__main__':
    app.run(debug=False, host=IMAGE_SERVICE_IP, port=IMAGE_SERVICE_PORT)