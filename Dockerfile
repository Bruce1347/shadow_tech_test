FROM python:3.12

RUN useradd app

RUN mkdir -p /home/app

COPY . /home/app

RUN chown app:app -R /home/app

USER app

WORKDIR /home/app

RUN pip install --user poetry

RUN /home/app/.local/bin/poetry install

EXPOSE 8000

ENTRYPOINT [ "bash", "/home/app/start_api.sh" ]