#!/bin/sh

if [ -z ${WORKERNAME+x} ]; then
        WORKERNAME=$HOSTNAME
fi

if [ -z ${BENCHMARK+x} ]; then
        BENCHMARK=false
fi

echo "WALLET: $WALLET"
echo "WORKERNAME: $WORKERNAME"
echo "BENCHMARK: $BENCHMARK"

if [ "$BENCHMARK" = true ]; then
        rm /benchmarks.json
fi

python3 cpuminer_driver.py $WALLET $WORKERNAME
