FROM python:3.6-alpine
LABEL maintainer="diminator"

ARG VERSION

RUN apk add --no-cache --update\
    build-base \
    gcc \
    gettext\
    gmp \
    gmp-dev \
    libffi-dev \
    openssl-dev \
    py-pip \
    python3 \
    python3-dev \
  && pip install virtualenv

COPY . /chatbots
WORKDIR /chatbots

# Only install install_requirements, not dev_ or test_requirements
RUN pip install -e .

# config.ini configuration file variables
ENV SLACK_BOT_NAME=''
ENV SLACK_BOT_TOKEN_maestro=''
ENV BDB_URI='https://test.bigchaindb.com'
ENV SPOTIFY_USER=''
ENV SPOTIFY_CLIENT_ID=''
ENV SPOTIFY_CLIENT_SECRET=''

ENTRYPOINT ["/chatbots/docker-entrypoint.sh"]
