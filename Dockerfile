FROM python:3.10-slim
EXPOSE 8000

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONFAULTHANDLER 1

COPY app.py /src/
COPY requirements.txt /src/
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libpq-dev python-dev \
    && pip install -r /src/requirements.txt
WORKDIR /src
CMD [ "flask", "run", "--port=8000" ]