To build, navigate to the /ip-docker directory and use:

`docker build -t ip_service .`

To run flask app use:

`docker run -p 5000:5000 ip_service`

To test, run the container and nagivate to tests then:

`python processing_test.py`
