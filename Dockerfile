FROM python:3.6-alpine

WORKDIR /app

ADD . /app

RUN apk update \
    && apk add sqlite \
    && apk add socat \
    && apk add python3-dev \
    && apk add libffi-dev \
    && apk add openssl-dev \
    && apk add zlib-dev \
    && apk add make \
    && apk add gcc

RUN pip install -r requirements.txt

CMD ["python", "bot.py"]

