# Cofig for running our app using Gunicorn

from dotenv import load_dotenv
import os

load_dotenv()
IMAGE_SERVICE_IP = os.getenv("HOST_IP") or "0.0.0.0"
IMAGE_SERVICE_PORT = os.getenv("PORT") or 5002

bind = f"{IMAGE_SERVICE_IP}:{IMAGE_SERVICE_PORT}"
workers = 2 # formula is 2*(No_of_cores) + 1 depending on the infra?
worker_class = "gevent"
timeout = 1200
loglevel = 'debug'
