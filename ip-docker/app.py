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
SPOOF_CLASSIFY = True # if this flag is set pretend to classify locally, will not make any external http calls
ID_LENGTH = 8

app = Flask(__name__)
CORS(app) # allow cross origin requests 
sock = Sock(app) # create a websocket

request_status = {} # holds the id and status of all current (and past) jobs
status_lock = Lock()
result_geojson = {} 


@app.route("/")
def home():
    return "<h1>Processing Server</h1>"

@sock.route('/ws-process')
def ws_process(ws):
        data = ws.receive()
        progress = {"status":"ACCEPTED"}
        # validate request
        if not validate_process_request_json(data):
            ws.send('invalid request, killing connection')
            return
        ws.send(progress)

        # pre-process 
        progress["status"] = "PROCESSING"
        ws.send(progress)
        processed_array = processImgFromLocal('tests/res/example_input_image.tif') # TODO THIS DOESNT DOWNLOAD FROM S3

        # classify
        progress["status"] = "CLASSIFYING"
        ws.send(progress)
        classified_array = spoof_classify(processed_array) # TODO THIS IS ALSO FAKE

        # post-process
        progress["status"] = "BUILDING"
        ws.send(progress)
        geojson = spoof_build_geojson(classified_array)
        
        progress["status"] = "DONE"
        progress["geojson"] = geojson
        ws.send(progress)

# validate that the incoming json has all the required fields
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
    raise NotImplementedError

# call the classification service
def classify(processed_array):
    raise NotImplementedError

# spoof building the geojson
def spoof_build_geojson(classified_output):
    with open('tests/res/labels.geojson') as fd:
        geojson = json.load(fd)
    return geojson

# pretend to call classification with sample data
def spoof_classify(array):
    with open('tests/res/classification_test_result.dump', 'rb') as fd:
        output = pickle.load(fd)
        return output
