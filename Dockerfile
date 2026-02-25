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

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app
#COPY app/ /app
# COPY template.html /app/template.html
# COPY entrypoint.sh /entrypoint.sh

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN addgroup -S app && adduser -S -G app app && \
    mkdir -p /app/output && chown -R app:app /app

USER app

ENTRYPOINT ["/entrypoint.sh"]
