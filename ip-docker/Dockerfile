FROM python:3.9-slim-buster
WORKDIR /ip_service
COPY requirements.txt requirements.txt
# cv2 dependencies
RUN apt-get update && apt-get install ffmpeg libsm6 libxext6  -y

RUN pip install -r requirements.txt
COPY . .
CMD ["flask", "run", "--host", "0.0.0.0", "--debugger"]

