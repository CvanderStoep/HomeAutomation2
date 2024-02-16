# Home Automation Project 
(HUE, INFLUXDB, SOLARPANEL, GRAFANA, DOCKER, DOCKER COMPOSE)
### Get live data from the following sources:
* City weather data using openweathermap api
* City weather data from buienradar
* City weather data from meteoserver
* Hue light sensor data
* Hue temperature sensor data
* Solarpanel data from Inverter

#### Output is send to InfluxDB (inside a Docker Container)
#### Output is visualized using Grafana (inside a Docker Container)
#### Realtime monitoring runs inside a Docker Container
#### check file private_info.py for correct computer address

####start the Containers: docker compose up --build
####op de RP: sudo docker-compose up --build


##install docking on raspberry pi
* apt-get update -y
* apt install docker.io -y && apt install docker-compose -y
##bring up docker
* docker-compose up --build
##clone files from github
* git clone https://github.com/CvanderStoep/HomeAutomation2

