# base image
FROM python:3.6-buster
ENV PYTHONUNBUFFERED 1

# set working directory
RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

RUN apt-get install -y gcc libc-dev git

RUN pip3 install --upgrade pip

RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y --default-toolchain nightly && cp $HOME/.cargo/bin/* /usr/bin/

ENV RUSTFLAGS="-C target-feature=-crt-static"

# add requirements
COPY ./requirements.txt /usr/src/app/requirements.txt

# install requirements
RUN pip3 install -r requirements.txt

RUN apt-get remove -y gcc libc-dev git

# add app
COPY . /usr/src/app
