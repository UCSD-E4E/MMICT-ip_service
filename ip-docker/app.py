"""

"""
from flask import Flask, request, make_response
from flask_cors import CORS
import requests
import random
import string
import pickle # only needed for testing without classification service
import json
from threading import Thread, Lock
from util.S3ImgGetter import getImg
from flask_sock import Sock

from util.image_processor import processImgFromLocal
from util.image_processor import processImgFromS3

import asyncio
import websockets

app = Flask(__name__)
CORS(app) # allow cross origin requests 
sock = Sock(app) # create a websocket

request_status = {} # holds the id and status of all current (and past) jobs
status_lock = Lock()
result_geojson = {} 


@app.route("/")
def home():
    asyncio.run(classify([1,2,3]))
    # nosync_classify([])
    return "<h1>Processing Server</h1>"

# route for accepting an incoming websocket request
@sock.route('/ws-process')
def ws_process(ws):
        # recieve the websocket data
        data = ws.receive()
        progress = {"status":"ACCEPTED"}

        # validate request matches expected json format
        if not validate_process_request_json(data):
            ws.send('invalid request, killing connection')
            return
        ws.send(progress)

        # pre-process data to prepare for classification
        progress["status"] = "PROCESSING"
        ws.send(progress)
        processed_array = processImgFromLocal('tests/res/example_input_image.tif') # TODO THIS DOESNT DOWNLOAD FROM S3

        # classify and write back current status on websocket
        progress["status"] = "CLASSIFYING"
        ws.send(progress)
        classified_array = classify(processed_array) 
        
        # build geojson from classified data
        progress["status"] = "BUILDING"
        ws.send(progress)
        geojson = spoof_build_geojson(classified_array) # TODO GEOJSON BUILDER IS NOT WORKING, THIS IS SPOOFING THE BUILDING PROCESS
    
        # notify and return geojson, then close the connection
        progress["status"] = "DONE"
        progress["geojson"] = geojson
        ws.send(progress)
        ws.close()

# validate that the json has all the required fields
# Note: This only checks that the required fields exists and ignores any additinoal fields
def validate_process_request_json(data):
    app.logger.warning("validating request: " + data)
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
def build_geojson(classified_output):
    # TODO fix the 
    raise NotImplementedError

# takes a processed_array and classifies it using a websocket connection to the classificaiton service
async def classify(processed_array):
    try:    
        async with websockets.connect("ws://192.168.1.195:5001/ws-classify") as websocket:
            req = {"classifier_id":13, "image_data":processed_array}
            await websocket.send(json.dumps(req))
            while(True): 
                message = await websocket.recv()
                app.logger.warning("recieved from ws: " + message)
                if message == "DONE":
                    break
    except Exception as e:
        app.logger.error(e)
        return []

# def nosync_classify(processed_array):  
#     try:
#         # ws = websockets.connect("ws://127.0.0.1:5001/ws-classify")
#         # req = {"classifier_id":13, "image_data":processed_array}
#         # ws.send("ASYNC IS FOR FOOLS!!!")
#         # message = ws.recv()
#         # app.logger.warning("recieved from ws: " + message)
#         # return message
#         pass
#     except Exception as e:
#         app.logger.error(e)
#         return []

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
