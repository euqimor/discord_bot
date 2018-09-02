FROM python:3.6-alpine

WORKDIR /app

ADD . /app

RUN apk update \
    && apk add sqlite \
    && apk add socat

RUN pip install -r requirements.txt

CMD ["python", "bot.py"]

