# docker-cpu-miner

Docker image for running the cpu-miner-opt by JayDDee
https://github.com/JayDDee/cpuminer-opt

## Usage

You can use the `WALLET` and `WORKERNAME` environment variables to configure which wallet to mine to and to set the worker name that will be passed along.

`docker run --restart unless-stopped -d -e WALLET='3KAKffgMS6JzNA5oa6C19zGXJgQbZxSFo6' -e WORKERNAME=worker1 NAME_OF_THE_CONTAINER`

