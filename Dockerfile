FROM ubuntu

RUN echo "deb http://archive.ubuntu.com/ubuntu precise main universe" > /etc/apt/sources.list
RUN apt-get update
RUN apt-get upgrade -y

RUN apt-get install -y python python-setuptools python-pip git
RUN easy_install redis 
RUN pip install etcd-py requests

# health check deps
RUN apt-get install -y curl telnet

RUN cd /opt && git clone https://github.com/transitorykris/etcd-py.git
RUN cd /opt/etcd-py && python setup.py install

ADD ./start.py /opt/start.py

CMD /usr/bin/python /opt/start.py
