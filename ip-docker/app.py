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
from util.image_processor import processImgFromLocal
from util.image_processor import processImgFromS3
SPOOF_CLASSIFY = True # if this flag is set pretend to classify locally, will not make any external http calls
ID_LENGTH = 8

app = Flask(__name__)
CORS(app) # allow cross origin requests 

request_status = {} # holds the id and status of all current (and past) jobs
status_lock = Lock()
result_geojson = {} 

@app.route("/")
def home():
    return "<h1>Processing Server</h1>"


# creates worker thread to handle request and responds 202 Accepted
@app.route("/process", methods=['POST'])
def process():
    content_type = request.headers.get('Content-Type')
    if content_type == 'application/json':
        json = request.json
        if('img_ref' not in json):
            return ("img_ref REQUIRED in body", 400)

        # parses image ref and starts processing
        img_ref = json['img_ref']
        id = runImgProcessThread(img_ref)
        with status_lock:
            request_status[id] = "CREATED"
        return (id, 202)
    else:
        return ("Internal Server Error",500)


# get status of id from dict
@app.route("/status/<id>", methods=['GET'])
def status(id):
    status_val = None
    with status_lock:
        if(id not in request_status):
            return ("invalid id",400)
        status_val = request_status[id]
    return (status_val,200)

# get status of result from dict
@app.route("/result/<id>", methods=['GET'])
def result(id):
    if(id not in result_geojson):
        return ("invalid id",400)
    geojson = result_geojson[id]
    return (geojson,200)



# create and run thread to processess image, return ID of thread
def runImgProcessThread(img_ref):
    id = getUID()
    t = Thread(target=imgProcessThread, args=(id, img_ref))
    t.start()
    return id

# process the image, updates the request_status as it goes
def imgProcessThread(id, img_ref):
    # set intial status
    with status_lock:
        request_status[id] = "PROCESSING"
    # Getting around S3 for development and testing
    if(img_ref == 'SPECIAL_TEST_CODE'):
        processed_array = processImgFromLocal('tests/res/example_input_image.tif')
    else:
        processed_array = processImgFromS3(img_ref)

    # "call classification"
    with status_lock:
        request_status[id] = "CLASSIFYING"
    classified_output = classify(processed_array)
    # build geojson
    with status_lock:
        request_status[id] = "FINISHING"
    geojson = build_geojson(classified_output)

    # make the geojson available
    result_geojson[id] = geojson
    with status_lock:
        request_status[id] = "READY"    
    return


def build_geojson(classified_output):
    if(SPOOF_CLASSIFY):
        with open('tests/res/labels.geojson') as fd:
            geojson = json.load(fd)
        return geojson
    raise NotImplementedError

# call classification service
def classify(array):
    if(SPOOF_CLASSIFY):
        # fake classify to test without classification service
        with open('tests/res/classification_test_result.dump', 'rb') as fd:
            output = pickle.load(fd)
            return output
        
    raise NotImplementedError



# Generates UID of length ID_LENGTH out of ascii chars
def getUID():
    return ''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase) for _ in range(ID_LENGTH))