# Web Engineering 2 App
## Recipe App for Web Engineering 2 at DHBW Mannheim
This is a simple Recipe App built with FastAPI for Web Engineering 2 at DHBW Mannheim. It allows users to create, read and delete recipes.
## Installation
I recommend using docker to run this app. You can also run it locally, but you need to install the dependencies first.
### Docker
1. Install Docker (https://docs.docker.com/get-docker/)
#### use the latest image from Docker Hub
2. Run the following command to start the app:
```bash
docker-compose -f docker-compose.yml up -d
```
#### build the image from the Dockerfile
3. Run the following command to build the image:
```bash
docker-compose -f docker-compose-dev.yml up -d
```

> Note: To stop the app, run `docker-compose down`. Sometimes `docker-compose` does not exist try `docker compose` instead.
## Warning
> :warning: This app is not production ready. It is only for educational purposes and should not be used in a production environment.
> Please note, that the authentication SECRET_KEY is currently stored in plain text in the `auth_handler.py` file. Please replace "your_secret_key" with a secure key before using this app in a production environment.

## Code Documentation
visit https://pixelwelt.github.io/WebEng-2-Projekt/ for a detailed documentation of the code.

