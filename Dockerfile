# Specify which base layers (default dependencies) to use
# You may find more base layers at https://hub.docker.com/
FROM python:3.7 as base


COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt


FROM base as final
#
# Creates directory within your Docker image
RUN mkdir -p /app/src/
RUN mkdir -p /app/model/
RUN mkdir -p /app/data/
#
# Copies file from your Local system TO path in Docker image
COPY . /app/src/
#
# Enable permission to execute anything inside the folder app
RUN chgrp -R 65534 /app && \
    chmod -R 777 /app

WORKDIR /app

# for serving default command
CMD ["uvicorn", "src.serve:app", "--host", "0.0.0.0", "--port", "8080"]   
