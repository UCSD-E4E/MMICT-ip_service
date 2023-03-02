from flask import Flask, request
import requests
from service.S3ImgGetter import getImg
from service.ImgProcessor import processImg

app = Flask(__name__)


@app.route("/")
def home():
    return "<h1>Home</h1>"


@app.route("/ip-service/process", methods=['post'])
def process():
    content_type = request.headers.get('Content-Type')
    if content_type == 'application/json':
        img_ref = 'example_input_image.tif'
        img = getImg(img_ref)
        processed_img = processImg(img)
        # Todo: send processed image to classification service

        return 'Process complete!'
    else:
        return 'Content-Type not supported!'


# flask examples
# #/api/blue?name=name
# @app.route("/api/blue", methods=['GET'])
# def blue():
#     if request.method != 'GET':
#         return "<script>alert('invalid method')</script>"
#     elif 'name' in request.args:
#         return f"<h1 style='color:blue'>BlueServer says hello {request.args['name']}!</h1>"
#     else:
#         return "<script>alert('invalid query string')</script>"

# #/api/blue?name=name
# @app.route("/api/jsonBlue", methods=['POST'])
# def jsonBlue():
#     content_type = request.headers.get('Content-Type')
#     if (content_type == 'application/json'):
#         json = request.json
#         json['visitedBlue'] = 'true'
#         return json
#     else:
#         return 'Content-Type not supported!'


# if __name__ == '__main__':
#     app.run(debug=True, port=5001)
