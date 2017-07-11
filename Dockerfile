FROM    python:alpine

RUN     mkdir /sc

WORKDIR  /sc

ADD . .

RUN     pip install -r requirements.txt

VOLUME  /sc
EXPOSE  80

ENTRYPOINT sh -c "gunicorn -b 0.0.0.0:80 --reload 'sc.wsgi';sh"
