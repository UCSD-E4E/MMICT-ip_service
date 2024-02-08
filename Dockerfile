# FOR ARM64, we are using Python 3.9.18 on Debian 12
FROM --platform=linux/amd64 python:3.9-slim-bookworm

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       ffmpeg \
       libsm6 \
       libxext6 \
       binutils \
       libproj-dev \
       gdal-bin \
       libgdal-dev \
       curl

# Environment variables for GDAL
ENV CPLUS_INCLUDE_PATH=/usr/include/gdal \
    C_INCLUDE_PATH=/usr/include/gdal

# Install Poetry
RUN python3.9 -m pip install poetry

WORKDIR /ip_service

# Copy all application files, make sure the poetry toml and .lock file are in the same directory
COPY . /ip_service/

# Install project dependencies
RUN poetry config virtualenvs.create false && poetry install --no-interaction --no-ansi

EXPOSE 8080

# poetry entrypoint to run the service
ENTRYPOINT ["/usr/local/bin/image-processing-server"]