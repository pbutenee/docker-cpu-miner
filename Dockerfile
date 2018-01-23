FROM ubuntu:16.04

# Copy run script
COPY configureAndMine.sh /

# Download miner
ADD https://github.com/JayDDee/cpuminer-opt/archive/v3.7.10.zip /v3.7.10.zip


# Install dependencies
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y build-essential libssl-dev libcurl4-openssl-dev libjansson-dev libgmp-dev automake unzip && \

# Build cpu miner
    unzip v3.7.10.zip && \
	rm v3.7.10.zip && \
	mv cpuminer-opt-3.7.10 cpuminer-opt && \
	cd /cpuminer-opt && \
	./build.sh && \
	chmod +x /configureAndMine.sh

ARG WALLET=35LdgWoNdRMXK6dQzJaJSnaLw5W3o3tFG6
ENV WALLET $WALLET

ENTRYPOINT /configureAndMine.sh
