FROM python:3.12-alpine

RUN apk add --no-cache \
    build-base \
    libffi-dev \
    zlib-dev \
    jpeg-dev \
    tiff-dev \
    freetype-dev \
    lcms2-dev \
    openjpeg-dev \
    libpng-dev \
    p7zip \
    ttf-dejavu \
    fontconfig

WORKDIR /app
#COPY app/ /app
# COPY template.html /app/template.html
# COPY entrypoint.sh /entrypoint.sh

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

ENTRYPOINT ["/entrypoint.sh"]
