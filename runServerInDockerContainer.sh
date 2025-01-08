#!/bin/bash

# Install Docker and Docker Compose
sudo apt update
sudo apt install -y docker docker-compose
sudo apt install docker-compose-plugin
docker-compose --version

# Build and run the Docker container
sudo docker-compose up --build || sudo docker compose up --build
