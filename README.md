# docker-cpu-miner

Docker image for running the cpu-miner-opt by JayDDee
https://github.com/JayDDee/cpuminer-opt

## Build

Clone the source code, go into the folder and build the container using the following command:

`docker build . -t cpu-miner`

## Usage

You can use the `WALLET` and `WORKERNAME` environment variables to configure which wallet to mine to and to set the worker name that will be passed along.

`docker run --restart unless-stopped -d -e WALLET='35LdgWoNdRMXK6dQzJaJSnaLw5W3o3tFG6' -e WORKERNAME=worker1 cpu-miner`

