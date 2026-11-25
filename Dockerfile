# FROM python:3.13.8  
FROM python:3.14-slim
# 3.10.6
# Below is executed to create the image
WORKDIR /usr/src/app

# Logregels direct doorgeven aan `docker logs` (niet bufferen)
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .

COPY config.cfg .
COPY *.py ./
# private_info.py en .python_hue worden via docker-compose gemount (zie .dockerignore)

RUN pip install --no-cache-dir -r requirements.txt

# Below is executed at the start of the container from the image
CMD ["python", "realtimemonitoring.py"]