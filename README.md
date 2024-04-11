********************

For running with the dummy-upload branch pipeline, see the README.md in the Web Server, which contains instructions for 
running the complete pipeline.

*********************

To build, navigate to the /ip-docker directory and use:

`docker build -t ip_service .`

To run flask app use:

`docker run -p {HOST_MACHINE_PORT}:5000 ip_service`

For example, running the following makes the service accessible at http://localhost:8080

`docker run -p 8080:5000 ip_service`

For testing with the central webserver, follow the build instructions for the webserver and run the following:

`docker run -p 8080:5000 --net=mmict_bridge ip_service`