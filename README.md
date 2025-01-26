# this OR that

Telegram mini-app where you have to choose one of two things.

## Installation

1. Installing the repository:
```bash
git install https://github.com/IgorVolochay/thisORthat
```

2. The project is written in Python3.9. Make sure you have it on your system. Go to the project folder, create a virtual environment and download pip requirements:
```bash
cd ./thisORthat
python3.9 -m venv venv
source ./venv/bin/activate
pip3 install -r requirements.txt
```

3. Installing MongoDB database. You can use the [official manual](https://www.mongodb.com/docs/manual/installation/) to install MongoDB manually, or use a [Docker image](https://hub.docker.com/r/mongodb/mongodb-community-server) to run the container:
```bash
docker run --name mongodb -d -p 27017:27017 mongodb/mongodb-community-server
```
