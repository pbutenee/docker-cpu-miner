# Autoswitching Nicehash CPU Miner

Docker image for running an autoswitching CPU miner for Nicehash. The code is based on the cpu-miner-opt by JayDDee
https://github.com/JayDDee/cpuminer-opt

## Usage

You can use the `WALLET` and `WORKERNAME` environment variables to configure which wallet to mine to and to set the worker name that will be passed along. Use the '-v' to point the container to a folder where the benchmark results can be stored, for example the current folder.

`docker run --restart unless-stopped -d -e WALLET='35LdgWoNdRMXK6dQzJaJSnaLw5W3o3tFG6' -e WORKERNAME=worker1 -v ${pwd}:/host_files/ pbutenee/docker-cpu-miner`

This will first run a benchmark afther which it will start mining and it will save the `benchmarks.json` file locally so that it can be used with new versions of the container without the need to rerun the benchmarks. To force the benchmark again just remove the `benchmarks.json` file.

While running, the script will update the hash rates based on the actual hash rates of the algorithm. So small mistakes in the benchmark will be corrected while running. The optimal number of threads however is never updated and benchmark mistakes that are more than 20% will most likely not be corrected.
