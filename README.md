To build, navigate to the /ip-docker directory and use:

`docker build -t ip_service .`

To run flask app use:

If you're running on MacOS, use port 8080 or something else instead. For some reason port 5000 does not work.
Example: `docker run -p 8080:5000 ip_service`

`docker run -p 5000:5000 ip_service`

