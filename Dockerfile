FROM python:3.8-alpine

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
    && apk add gcc \
    && apk add jpeg-dev \
    && apk add freetype-dev \
    && apk add lcms2-dev \
    && apk add openjpeg-dev \
    && apk add tiff-dev \
    && apk add tk-dev \
    && apk add tcl-dev

RUN pip install -r requirements.txt

CMD ["python", "bot.py"]

