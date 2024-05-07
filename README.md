To build, navigate to the /ip-docker directory and use:

`docker build -t ip_service .`

To run flask app use:

`docker run -p {HOST_MACHINE_PORT}:5000 ip_service`

For example, running the following makes the service accessible at http://localhost:8080

`docker run -p 8080:5000 ip_service`

For testing with the central webserver, follow the build instructions for the webserver and run the following:

`docker run -p {HOST_MACHINE_PORT}:5000 --net=mmict_bridge ip_service`

## Setting the S3 Access Config
In `ip-docker/util/s3_access.cfg`, copy paste the following:

- [AWS_S3]
- bucket_name = testlawrence
- aws_access_key_id = **ASK IN THE CHANNEL**
- aws_secret_access_key = **ASK IN THE CHANNEL**