"""

"""
from flask import Flask, request, make_response
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
        response = make_response()
        response.status_code = 202
        response.status = "Accepted"
        return response
    else:
        response = make_response()
        response.status_code = 500
        return response


# get status of d
@app.route("/status", methods=['GET'])
def status():
    img_id = request.args.get('id')



    response = make_response(f'<h1>echo {img_id}</h1>')
    response.status_code = 
    print(Hello world) 
    response.status = "Bad Request"

    return response

