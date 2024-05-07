"""

"""
import asyncio  
import json  
import logging  
import requests
import pickle  # only needed for testing without classification service  
import random  
import string  
import websockets

import os
from dotenv import load_dotenv
from threading import Lock, Thread  

import requests  
import websockets  
from flask import Flask, make_response, request  
from flask_cors import CORS  
from flask_sock import Sock  

# Ultility functions from the util directory  
from mm_image_processing.util import image_processor  
from mm_image_processing.util.image_processor import processImgFromLocal  
from mm_image_processing.util.s3_img_getter import deleteImg, getImg

logging.basicConfig(level=logging.DEBUG)
load_dotenv()

app = Flask(__name__)
sock = Sock(app)  # create a websocket
CORS(app)  # allow cross origin requests

# IP and port address of the classification service
CLASSIFY_IP = "100.64.112.224" # "container-service"
CLASSIFY_PORT = "5000"
IMAGE_SERVICE_IP = os.getenv("HOST_IP")
IMAGE_SERVICE_PORT = os.getenv("PORT")

# used to test if the server is up and running
@app.route("/")
def home():
    return "<h1>Processing Server</h1>"

# for testing websocket connections
@sock.route('/echo')
def ws_echo(ws):
    app.logger.debug("received echo request")
    while (True):
        data = ws.receive()
        ws.send("Process Server is echoing: " + data)


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
    request_json = json.loads(data)
    classifier_id = request_json['classifier_id']
    img_ref = request_json['image_ref']

    # write back progress update on the websocket
    progress = {"status": "ACCEPTED"}
    msg = json.dumps(progress)
    ws.send(msg)

    # write back progress again
    progress["status"] = "DOWNLOADING"
    msg = json.dumps(progress)
    ws.send(msg)

    # try to download the image at img_ref from the s3 bucket
    try:
        imgUrl = getImg(img_ref)
    except Exception as e:
        app.logger.error(e)
        ws.close(1)
        return
    
    # write back progress again
    progress["status"] = "PROCESSING"
    msg = json.dumps(progress)
    ws.send(msg)

    # process the image now that it is downloaded locally
    img_shape, bbox, processed_array = processImgFromLocal(imgUrl)

    # write back progress update
    progress["status"] = "CLASSIFYING"
    # progress["bbox"] = bbox # write bbox back for debugging purpose only
    msg = json.dumps(progress)
    ws.send(msg)

    # call the classify() method to get classified data from classification_service
    # * asyncio set so this route does not need to be an async function *
    asyncio.set_event_loop(asyncio.new_event_loop())
    classified_array = asyncio.get_event_loop().run_until_complete(
        classify(classifier_id, processed_array))  # NOTE use await instead of this since it is cleaner

    # check if classify() method failed
    if classified_array is None:
        ws.send('classification_service error')
        ws.close(1)
        return
    

    # write back progress update
    progress["status"] = "BUILDING"
    msg = json.dumps(progress)
    ws.send(msg)

    # build geojson from classified data, then convert to a serializable json format
    geojson_raw = build_geojson(img_shape, bbox, classified_array)
    geojson = geojson_raw.to_json()

    # final writeback on websocket, then close connection
    progress["status"] = "DONE"
    progress["geojson"] = geojson    
    msg = json.dumps(progress)
    ws.send(msg)
    ws.close()


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
        request_json = json.loads(data)
        if 'processor_id' not in request_json:
            app.logger.warning("no processor_id")
            return False
        if 'classifier_id' not in request_json:
            app.logger.warning("no classifier_id")
            return False
        if 'image_ref' not in request_json:
            app.logger.warning("no image_ref")
            return False
        return True
    except Exception as e:
        app.logger.error(e)
        return False


# build a geojson object from the classified output 
def build_geojson(img_shape, bbox, classified_output):
    return image_processor.buildGeoJson(img_shape, bbox, classified_output, app.logger.warning)

async def classify(classifier_id, processed_array):
    """
    Takes a processed array and classifies it over a WebSocket connection to the classification service.

    Args:
        classifier_id (str): The ID of the classifier to use for classification.
        processed_array (ndarray): The processed array to classify.

    Returns:
        str or None: The classified result as a string if successful, None in the case of an error.
    """

    app.logger.debug("trying to connect to ws")
    try:
        async with websockets.connect("ws://" + CLASSIFY_IP + ":" + CLASSIFY_PORT + "/ws-classify", max_size=2 ** 30) as websocket:
            # send request to classifier
            req = {"classifier_id": classifier_id, "image_data": processed_array.tolist()}
            await websocket.send(json.dumps(req))

            # check for ACCEPTED response
            message = await websocket.recv()
            app.logger.debug("recieved from ws: " + message)
            if message != "ACCEPTED":
                app.log.error("classifier rejected request")
                return None

            # check for DONE response indicating next message is the array
            message = await websocket.recv()
            app.logger.debug("recieved from ws: " + message)
            if message != "DONE":
                app.log.error("Classifier failed")
                return None
            
            # get classified array and return it
            result = await websocket.recv()
            app.logger.debug("recieved from ws: " + result)
            return result
        
    # generic exception catching
    except Exception as e:
        app.logger.error(e)
        return None


# spoof building the geojson since it broke
def spoof_build_geojson(classified_output):
    app.logger.warning("Using spoofed geojson")
    with open('tests/res/labels.geojson') as fd:
        geojson = json.load(fd)
    return geojson

# pretend to call classification with sample data
def spoof_classify(array):
    with open('tests/res/classification_test_result.dump', 'rb') as fd:
        output = pickle.load(fd)
        return output
    
# callable function to run server, included this in order to define our poetry entrypoint
def main():
    app.run(debug=False, port=IMAGE_SERVICE_PORT, host=IMAGE_SERVICE_IP)