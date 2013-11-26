FROM ubuntu

RUN echo "deb http://archive.ubuntu.com/ubuntu precise main universe" > /etc/apt/sources.list
RUN apt-get update
RUN apt-get upgrade -y

RUN apt-get install -y python python-setuptools
RUN easy_install redis 

# health check deps
RUN apt-get install -y curl telnet


ADD ./start.py /opt/start.py

CMD ["/usr/bin/python", "/opt/start.py"]
