FROM python:3-slim

RUN pip install poetry

WORKDIR /src

COPY . /src

RUN poetry build -f wheel \
  && pip install ./dist/git_info-*-py3-none-any.whl

RUN rm -rf /src

ENTRYPOINT ["gitinfo"]
