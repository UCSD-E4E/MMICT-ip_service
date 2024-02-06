# FOR ARM64, 
FROM --platform=linux/amd64 python:3.9-slim-buster

WORKDIR /ip_service

# Install system dependencies required for Poetry and your project
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

# Set environment variables for GDAL
ENV CPLUS_INCLUDE_PATH=/usr/include/gdal \
    C_INCLUDE_PATH=/usr/include/gdal

# Install Poetry
RUN pip install poetry

# Ensure that Poetry is in the PATH
ENV PATH="${PATH}:/root/.poetry/bin"

# Copy only pyproject.toml and poetry.lock (if available) to cache dependencies
COPY pyproject.toml poetry.lock* /ip_service/

# Install project dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi

# Copy the rest of the application
COPY . /ip_service/

EXPOSE 8080

# poetry entrypoint to run the service
CMD ["flask", "run", "--host", "0.0.0.0"]
