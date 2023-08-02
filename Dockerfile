FROM python:3.10.7
USER root

# ローカルでビルドをする際のコマンド
# docker build . -t discordfast:v0
# docker run --name discordfast -it discordfast:v0 /bin/bash

# 再ビルドをする場合必ずimageは削除すること
# docker rm discordfast

# 仮想環境の構築
# python3 -m venv venv
# .\venv\Scripts\activate
# pip install -r requirements.txt

# ディレクトリ ./appに移動
WORKDIR /app

RUN apt-get -y update && apt-get -y install locales && apt-get -y upgrade && \
    localedef -f UTF-8 -i ja_JP ja_JP.UTF-8
ENV LANG ja_JP.UTF-8
ENV LANGUAGE ja_JP:ja
ENV LC_ALL ja_JP.UTF-8
ENV TZ JST-9
ENV TERM xterm

# ./root/src ディレクトリを作成 ホームのファイルをコピーして、移動
RUN mkdir -p /root/src
COPY . /root/src
WORKDIR /root/src

# Docker内で扱うffmpegをインストール
RUN apt-get install -y ffmpeg

# pipのアップグレード、requirements.txtから必要なライブラリをインストール
RUN pip install --upgrade pip
RUN pip install --upgrade setuptools
RUN pip install -r requirements.txt
# discord.pyをpy-cordにアップグレード
RUN pip install git+https://github.com/Pycord-Development/pycord

# 以下はKoyebで運用する際に必要
# ポート番号8080解放
#EXPOSE 8080

# ディレクトリ /root/src/appに移動
#WORKDIR /root/src/app

# DiscordBotとFastAPIのサーバ起動
#CMD [ "python", "-u", "main.py" ]