# Autoswitching Nicehash CPU Miner

Docker image for running an autoswitching CPU miner for Nicehash. The code is based on the cpu-miner-opt by JayDDee
https://github.com/JayDDee/cpuminer-opt

## Usage

You can use the `WALLET` and `WORKERNAME` environment variables to configure which wallet to mine to and to set the worker name that will be passed along.

`docker run --restart unless-stopped -d -e WALLET='35LdgWoNdRMXK6dQzJaJSnaLw5W3o3tFG6' -e WORKERNAME=worker1 -v $(pwd):/host_files/ pbutenee/docker-cpu-miner`


## Benchmark

The container is benchmarked for an Intel i7-7700 Quad. If you want to benchmark your own CPU and select the optimal number of threads for your current setup use the `BENCHMARK` environment variable. This will take about 20 minutes.

`docker run --restart unless-stopped -d -e WALLET='35LdgWoNdRMXK6dQzJaJSnaLw5W3o3tFG6' -e WORKERNAME=worker1 -e BENCHMARK=true -v $(pwd):/host_files/ pbutenee/docker-cpu-miner`

While running, the script will update the hash rates based on the actual hash rates of the algorithm. So small mistakes in the benchmark will be corrected while running. The optimal number of threads however is never updated and benchmark mistakes that are more than 20% will most likely not be corrected.