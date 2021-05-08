FROM python:3.8-slim-buster

RUN apt-get update && \
    apt-get install -y python-pip \
    python-pil \
    python-lxml \
    git \
    wget \
    unzip

# clean apt-get
RUN apt-get autoclean && \
    apt-get clean && \
    apt-get autoremove

# update pip
RUN pip install -U pip setuptools

# INSTALL requirements before for caching
COPY requirements.txt /var/app/requirements.txt

# install requirements
RUN pip install -r /var/app/requirements.txt

WORKDIR /opt/

RUN git clone https://github.com/tensorflow/models
RUN  wget https://github.com/google/protobuf/releases/download/v3.3.0/protoc-3.3.0-linux-x86_64.zip \
     && chmod 775 protoc-3.3.0-linux-x86_64.zip \
     && unzip protoc-3.3.0-linux-x86_64.zip \
     && mv bin/protoc /usr/bin/
RUN cd models/research && protoc object_detection/protos/*.proto --python_out=. 

# APPLICATION
ADD . /opt/object_detection/

CMD ["python", "/opt/object_detection/object_detection_app_p3/app.py"] 