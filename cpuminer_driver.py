#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Cross-platform controller for NiceHash Excavator for Nvidia."""

# Example usage:
#   $ excavator -p 3456 &
#   $ sleep 5
#   $ python3 excavator-driver.py

__author__ = "Ryan Young"
__email__ = "rayoung@utexas.edu"
__license__ = "public domain"

import json
import logging
import signal
import socket
import sys
import urllib.error
import urllib.request
from time import sleep
import os.path
import subprocess

WALLET = '35LdgWoNdRMXK6dQzJaJSnaLw5W3o3tFG6'
WORKER = 'worker1'
REGION = 'eu' # eu, usa, hk, jp, in, br
BENCHMARKS_FILE = 'benchmarks.json'

PROFIT_SWITCH_THRESHOLD = 0.05
UPDATE_INTERVAL = 60

EXCAVATOR_TIMEOUT = 10
NICEHASH_TIMEOUT = 20



def nicehash_multialgo_info():
    """Retrieves pay rates and connection ports for every algorithm from the NiceHash API."""
    response = urllib.request.urlopen('https://api.nicehash.com/api?method=simplemultialgo.info',
                                      None, NICEHASH_TIMEOUT)
    query = json.loads(response.read().decode('ascii')) #json.load(response)
    paying = {}
    ports = {}
    for algorithm in query['result']['simplemultialgo']:
        name = algorithm['name']
        paying[name] = float(algorithm['paying'])
        ports[name] = int(algorithm['port'])
    return paying, ports

def nicehash_mbtc_per_day(benchmarks, paying):
    """Calculates the BTC/day amount for every algorithm.
    device -- excavator device id for benchmarks
    paying -- algorithm pay information from NiceHash
    """

    revenue = {}
    for algorithm in benchmarks:
        revenue[algorithm] = paying[algorithm] * benchmarks[algorithm]['hash_rate'] * (24*60*60) * 1e-11

    return revenue



def main():
    """Main program."""
    logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s',
                        level=logging.INFO)



    # benchmark if necessary
    if not os.path.isfile(BENCHMARKS_FILE):
        import benchmark
        paying, ports = nicehash_multialgo_info()
        benchmark.run(paying.keys())

    # load benchmarks
    benchmarks = json.load(open(BENCHMARKS_FILE))

    running_algorithm = None
    cpuminer_process = None

    while True:
        try:
            paying, ports = nicehash_multialgo_info()
        except urllib.error.URLError as err:
            logging.warning('failed to retrieve NiceHash stats: %s' % err.reason)
        except urllib.error.HTTPError as err:
            logging.warning('server error retrieving NiceHash stats: %s %s'
                            % (err.code, err.reason))
        except socket.timeout:
            logging.warning('failed to retrieve NiceHash stats: timed out')
        except (json.decoder.JSONDecodeError, KeyError):
            logging.warning('failed to parse NiceHash stats')
        else:
            payrates = nicehash_mbtc_per_day(benchmarks, paying)
            best_algorithm = max(payrates.keys(), key=lambda algo: payrates[algo])

            if running_algorithm == None or running_algorithm != best_algorithm and \
                (payrates[running_algorithm] or payrates[best_algorithm]/payrates[running_algorithm] >= 1.0 + PROFIT_SWITCH_THRESHOLD):

                # kill previous miner
                if cpuminer_process != None:
                    cpuminer_process.terminate()
                    logging.info('killed process running ' + running_algorithm)

                # start miner
                logging.info('starting mining using ' + best_algorithm + ' using ' + str(benchmarks[best_algorithm]['nof_threads']) + ' threads')
                cpuminer_process = subprocess.Popen(['./cpuminer', '-u', WALLET + '.' + WORKER, '-p', 'x',
                    '-o', 'stratum+tcp://' + best_algorithm + '.' + REGION + '.' + 'nicehash.com:' + str(ports[best_algorithm]),
                    '-a', best_algorithm, '-t', str(benchmarks[best_algorithm]['nof_threads'])])
                running_algorithm = best_algorithm

        sleep(UPDATE_INTERVAL)

if __name__ == '__main__':
    if len(sys.argv) > 0:
        WALLET = sys.argv[1]
    if len(sys.argv) > 1:
        WORKER = sys.argv[2]
    main()