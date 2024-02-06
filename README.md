To build, navigate to the /ip-docker directory and use:

`docker build -t ip_service .`

To run flask app use:

If you're running on MacOS, use port 8080 or something else instead. For some reason port 5000 does not work.
Example: `docker run -p 8080:5000 ip_service`

`docker run -p {HOST_MACHINE_PORT}:5000 ip_service`

For example, running the following makes the service accessible at http://localhost:8080

`docker run -p 8080:5000 ip_service`

For testing with the central webserver, follow the build instructions for the webserver and run the following:

`docker run -p {HOST_MACHINE_PORT}:5000 --net=mmict_bridge ip_service`
