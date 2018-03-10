FROM ubuntu:16.04

ARG MWS_ACCESS_KEY
ARG MWS_SECRET_KEY
ARG SELLER_ID

ENV MWS_ACCESS_KEY $MWS_ACCESS_KEY
ENV MWS_SECRET_KEY $MWS_SECRET_KEY
ENV SELLER_ID $SELLER_ID

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

RUN mkdir -p /winshares/user
COPY . /searcher
WORKDIR /searcher

RUN pip3.6 install requirements.txt

CMD []

