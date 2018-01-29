#!/bin/sh

if [ -z ${WORKERNAME+x} ]; then
        WORKERNAME=$HOSTNAME
fi


echo "WALLET: $WALLET"
echo "WORKERNAME: $WORKERNAME"


python3 cpuminer_driver.py $WALLET $WORKERNAME
