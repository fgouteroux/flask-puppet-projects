FROM python:2.7
ENV PYTHONUNBUFFERED 1
RUN mkdir /code
WORKDIR /code
ADD code /code/

RUN pip install -r /code/puppet-projects/requirements.txt
