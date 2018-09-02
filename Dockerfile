FROM python:3.6-alpine

WORKDIR /app

ADD . /app

RUN apk update \
    && apk add git \
    && apk add sqlite \
    && apk add socat \
    && apk add python3-dev \
    && apk add libffi-dev \
    && apk add openssl-dev \
    && apk add musl-dev \
    && apk add libxml2-dev \
    && apk add libxslt-dev \
    && apk add zlib-dev \
    && apk add make \
    && apk add gcc

RUN pip install -r requirements.txt

CMD ["python", "bot.py"]

