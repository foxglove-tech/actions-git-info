FROM python:3-slim

RUN pip install poetry

WORKDIR /src

RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/* /var/cache/apt/*

COPY . /src

RUN poetry build -f wheel \
  && pip install ./dist/git_info-*-py3-none-any.whl

COPY entrypoint.sh /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
