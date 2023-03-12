"""

"""
from flask import Flask, request
import requests
from util.S3ImgGetter import getImg


app = Flask(__name__)


@app.route("/")
def home():
    return "<h1>Processing Server</h1>"


# creates worker thread to handle request and responds 202 Accepted
@app.route("/process", methods=['POST', 'GET'])
def process():
    content_type = request.headers.get('Content-Type')
    if content_type == 'application/json':
        img_ref = 'example_input_image.tif'
        img = getImg(img_ref)
        # processed_img = processImg(img)
        # Todo: send processed image to classification service
        return 202, 'Accepted', {}
    else:
        return 500, 'Internal Error', {}


# get status of d
@app.route("/status", methods=['GET'])
def status():
    img_id = request.args.get('id')
    print(img_id)
    return 200, 'OK', {}

