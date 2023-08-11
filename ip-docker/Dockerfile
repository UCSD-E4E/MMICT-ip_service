# FROM python:3.9-slim-buster
# WORKDIR /ip_service
# COPY requirements.txt requirements.txt
# # cv2 dependencies
# RUN apt-get update && apt-get install ffmpeg libsm6 libxext6  -y

# RUN pip install -r requirements.txt
# COPY . .
# CMD ["flask", "run", "--host", "0.0.0.0", "--debugger"]

# FOR ARM64
FROM python:3.9-slim-bookworm
EXPOSE 8000
WORKDIR /ip_service
# cv2 dependencies
RUN apt-get update 
RUN apt-get install -y ffmpeg \
                        build-essential \
                        libsm6 \
                        libxext6 \
                        binutils \
                        libproj-dev \
                        gdal-bin \
                        libgdal-dev
ENV CPLUS_INCLUDE_PATH=/usr/include/gdal
ENV C_INCLUDE_PATH=/usr/include/gdal
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
COPY . .
#CMD ["flask", "run", "--host", "0.0.0.0"]
CMD ["python3", "-m", "gunicorn", "-w", "4", "app:app"]
