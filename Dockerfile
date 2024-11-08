# FOR x86_64 Pytorch 2.4.1 CUDA 12.1 w/ Ubuntu 20.04
FROM --platform=linux/amd64 pytorch/pytorch:2.4.1-cuda12.1-cudnn9-runtime

# Install system dependencies, included OpenGL support and Glib for Open CV
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       python3-pip \
       libproj-dev \
       gdal-bin \
       libgdal-dev \
       libgl1-mesa-glx \
       libglib2.0-0 \
       && apt-get clean \
       && rm -rf /var/lib/apt/lists/*

# Environment variables for GDAL
ENV CPLUS_INCLUDE_PATH=/usr/include/gdal \
    C_INCLUDE_PATH=/usr/include/gdal

RUN python3 --version || python --version

# Install Poetry & clear the pip cache
RUN python3 -m pip install poetry && rm -rf /root/.cache/pip

WORKDIR /ip_service

# Copy all application files, make sure the poetry toml and .lock file are in the same directory
COPY . /ip_service/

# Install project dependencies without virtual env, then clear the poetry cache
RUN poetry config virtualenvs.create false && poetry install --no-interaction --no-ansi && poetry cache clear --all pypi

EXPOSE 5002

# poetry entrypoint to run the service, this executable is stored in our Docker container's file system
CMD ["gunicorn", "-c", "gunicorn_config.py", "mm_image_processing.server:app"]