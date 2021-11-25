FROM python:3.9-slim 

ENV PYTHONFAULTHANDLER=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONHASHSEED=random
ENV PYTHONDONTWRITEBYTECODE 1
ENV PIP_NO_CACHE_DIR=off
ENV PIP_DISABLE_PIP_VERSION_CHECK=on
ENV PIP_DEFAULT_TIMEOUT=100

# Env vars
ENV TELEGRAM_TOKEN ${TELEGRAM_TOKEN}
ENV MODE ${MODE} 

RUN apt-get update
RUN apt-get install -y python3 python3-pip python-dev build-essential python3-venv

RUN mkdir -p /app /storage
ADD . /app

#RUN addgroup --gid 1024 telegram
#RUN useradd --badname --gid 1024 -u 5678 telegram
#RUN chown -R telegram:telegram /app
#RUN chown -R telegram:telegram /storage
RUN chmod +x /app/bot.py

WORKDIR /app
RUN pip3 install -r requirements.txt
#USER telegram:telegram

CMD python3 /app/bot.py
