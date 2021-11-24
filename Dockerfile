FROM python:3.8-slim AS bot

ENV PYTHONFAULTHANDLER=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONHASHSEED=random
ENV PYTHONDONTWRITEBYTECODE 1
ENV PIP_NO_CACHE_DIR=off
ENV PIP_DISABLE_PIP_VERSION_CHECK=on
ENV PIP_DEFAULT_TIMEOUT=100

# Env vars
ENV TELEGRAM_TOKEN ${TELEGRAM_TOKEN}

RUN apt-get update
RUN apt-get install -y python3 python3-pip python-dev build-essential python3-venv

RUN mkdir -p /app /storage
ADD . /app
WORKDIR /app

RUN pip3 install -r requirements.txt
RUN chmod +x /app/bot.py

CMD python3 /app/bot.py
