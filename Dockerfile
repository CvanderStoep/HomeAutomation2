#FROM python:3
FROM python:3.10.6
# Below is executed to create the image
WORKDIR /usr/src/app

COPY requirements.txt .
COPY config.cfg .
COPY *.py ./
COPY *.xlsx ./
#COPY *.py ./  #raspberry
COPY .python_hue .

RUN pip install --no-cache-dir -r requirements.txt

# Below is executed at the start of the container from the image
CMD ["python", "realtimemonitoring.py"]