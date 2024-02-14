# Docker Info

## Building our Docker image: 

Run this in the CLI: "docker build -t ip_service ."

## Running the Docker Container (For Devs):

Run this in the CLI: "docker run -p {HOST_MACHINE_PORT}:5000 ip_service"

For example, running the following makes the service accessible at http://localhost:8080.
Note: If you're running on MacOS, use port 8080 or something else instead. For some reason port 5000 does not work.

"docker run -p 8080:5000 ip_service"

For testing with the central webserver, follow the build instructions for the webserver and run the following:

"docker run -p {HOST_MACHINE_PORT}:5000 --net=mmict_bridge ip_service"

# Libraries and Dependencies:

Below is the preiouvs requirements.txt file:
(Still sorting through what will be required for our IP service)

Flask==2.3.1
requests==2.28.2
boto3==1.26.120
numpy==1.24.3
rasterio==1.3.6
rioxarray==0.14.1
xarray==2023.4.2
distancerasters==0.3.2
opencv-contrib-python==4.7.0.72
dask==2023.4.0
simplejson==3.19.1
Flask-Cors==3.0.10
flask-sock==0.6.0 
h11==0.14.0 
websockets==11.0.2
geopandas==0.12.2
pandas==1.5.3

