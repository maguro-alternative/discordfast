FROM python:3.10.7
USER root

# docker build . -t discordfast:v0
# docker run --name discordfast -it discordfast:v0 /bin/bash

WORKDIR /app

RUN apt-get -y update && apt-get -y install locales && apt-get -y upgrade && \
    localedef -f UTF-8 -i ja_JP ja_JP.UTF-8
ENV LANG ja_JP.UTF-8
ENV LANGUAGE ja_JP:ja
ENV LC_ALL ja_JP.UTF-8
ENV TZ JST-9
ENV TERM xterm

RUN mkdir -p /root/src
COPY . /root/src
WORKDIR /root/src

RUN apt-get install -y ffmpeg

RUN pip install --upgrade pip
RUN pip install --upgrade setuptools
RUN pip install -r requirements.txt
RUN pip install git+https://github.com/Pycord-Development/pycord