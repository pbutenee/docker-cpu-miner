#!/bin/sh

if [ -z ${WORKERNAME+x} ]; then
        WORKERNAME=$HOSTNAME
fi

echo "WALLET: $WALLET"
echo "WORKERNAME: $WORKERNAME"

cd cpuminer-opt
./cpuminer -u $WALLET.$WORKERNAME -t 4 -o stratum+tcp://cryptonight.eu.nicehash.com:3355 -p x -a cryptonight