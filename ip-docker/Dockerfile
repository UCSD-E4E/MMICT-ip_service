# FROM python:3.9-slim-buster
# WORKDIR /ip_service
# COPY requirements.txt requirements.txt
# # cv2 dependencies
# RUN apt-get update && apt-get install ffmpeg libsm6 libxext6  -y

# RUN pip install -r requirements.txt
# COPY . .
# CMD ["flask", "run", "--host", "0.0.0.0", "--debugger"]

# FOR ARM64
FROM --platform=linux/amd64 python:3.9-slim-buster
EXPOSE 5000
WORKDIR /ip_service
COPY requirements.txt requirements.txt
# cv2 dependencies
RUN apt-get update && apt-get install ffmpeg libsm6 libxext6  -y
RUN apt-get install -y binutils libproj-dev gdal-bin ffmpeg libgdal-dev
RUN export CPLUS_INCLUDE_PATH=/usr/include/gdal
RUN export C_INCLUDE_PATH=/usr/include/gdal
RUN pip install -r requirements.txt
COPY . .
CMD ["flask", "run", "--host", "0.0.0.0", "--debugger"]