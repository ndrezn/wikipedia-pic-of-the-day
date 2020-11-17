FROM ubuntu:latest

RUN apt-get update -y && apt-get install -y python3-pip python-dev

COPY ./requirements.txt /requirements.txt
COPY ./bot/ /bot/
COPY ./run.py /run.py

RUN pip3 install -r requirements.txt

ENTRYPOINT [ "python3" ]
CMD [ "run.py" ]
