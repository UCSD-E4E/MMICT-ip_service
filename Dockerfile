FROM python:3.9-slim-buster
WORKDIR /ip_service
COPY ./requirements.txt /ip_service
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
ENV FLASK_APP=server.py
CMD ["flask", "run", "--host", "0.0.0.0"]