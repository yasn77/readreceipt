FROM python:3.10-slim
EXPOSE 8000

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONFAULTHANDLER 1

COPY app.py /src/
COPY requirements.txt /src/
COPY migrations /src/
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libpq-dev python3-dev \
    && pip install -r /src/requirements.txt
WORKDIR /src
CMD [ "gunicorn", "--bind=0.0.0.0:8000", "app:app" ]
