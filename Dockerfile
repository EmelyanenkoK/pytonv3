FROM ubuntu:20.04

RUN apt-get update && \
    apt-get install -y wget git python3 python3-pip

RUN python3 -m pip install tvm_valuetypes aiohttp

EXPOSE 8080

WORKDIR /usr/src/pytonv3

ENV GETMETHODS false

COPY . /usr/src/pytonv3

CMD python3 -m pyTON --port 8080 --getmethods ${GETMETHODS} --liteserverconfig config.json 
