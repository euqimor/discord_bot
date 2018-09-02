FROM python:3.6-alpine

WORKDIR /app

ADD . /app

RUN apk update \
    && apk add sqlite \
    && apk add socat \
    && apk add python-dev \
    && apk add libffi-dev \
    && apk add openssl-dev \
    && apk add zlib-dev

RUN pip install -r requirements.txt

CMD ["python", "bot.py"]

