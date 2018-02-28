FROM ubuntu:16.04

RUN apt-get update
RUN apt-get install -y software-properties-common
RUN apt-get install -y wget

RUN apt-get install -y make build-essential libssl-dev zlib1g-dev
RUN apt-get install -y libbz2-dev libreadline-dev libsqlite3-dev wget curl llvm
RUN apt-get install -y libncurses5-dev  libncursesw5-dev xz-utils tk-dev

RUN wget https://www.python.org/ftp/python/3.6.3/Python-3.6.3.tgz && \
 tar xvf Python-3.6.3.tgz && \
 cd Python-3.6.3 && \
 ./configure --enable-optimizations && \
 make -j8 && \
 make altinstall && \
 cd ..

RUN apt-get update

RUN mkdir /home/amazon
RUN mkdir /home/amazon/data
RUN mkdir /home/amazon/code

COPY . /home/amazon/code
WORKDIR /home/amazon/code

RUN pip3.6 install requirements.txt

CMD []

