# Autoswitching Nicehash CPU Miner

Docker image for running an autoswitching CPU miner for Nicehash. The code is based on the cpu-miner-opt by JayDDee
https://github.com/JayDDee/cpuminer-opt

## Usage

You can use the `WALLET` and `WORKERNAME` environment variables to configure which wallet to mine to and to set the worker name that will be passed along.

`docker run --restart unless-stopped -d -e WALLET='35LdgWoNdRMXK6dQzJaJSnaLw5W3o3tFG6' -e WORKERNAME=worker1 pbutenee/docker-cpu-miner`


## Benchmark

If you want to benchmark your own CPU remove the benchmarks.json file and build the container again. It will also select the optimal number of threads for your current setup.

The file included are the benchmarks for an intel i7 7700 Quad.