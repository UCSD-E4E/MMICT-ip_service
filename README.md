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


