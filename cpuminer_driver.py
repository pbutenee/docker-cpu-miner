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
from time import sleep, time
import os.path
import subprocess
import threading
import numpy as np


WALLET = '35LdgWoNdRMXK6dQzJaJSnaLw5W3o3tFG6'
WORKER = 'worker1'
REGION = 'eu' # eu, usa, hk, jp, in, br
BENCHMARKS_FILE = '/host_files/benchmarks.json'

PROFIT_SWITCH_THRESHOLD = 0.05
UPDATE_INTERVAL = 60

# artificailly increase profit if it hasn't been updated ever or in the past 24h
PROFIT_INCREASE_TIME = 24 * 60 * 60    # s

# number of hashes needed to compute the actual measured hash rate
NOF_HASHES_BEFORE_UPDATE = 10000

EXCAVATOR_TIMEOUT = 10
NICEHASH_TIMEOUT = 20


class MinerThread(threading.Thread):
    def __init__(self, cmd, nof_threads):
        self.cmd = cmd
        self.hash_sum = np.zeros((nof_threads,))
        self.nof_hashes = np.zeros((nof_threads,))

        self.fail_count = 0
        self.last_fail_time = 0

        self.process = None
        threading.Thread.__init__(self)

    def run(self):
        with subprocess.Popen(self.cmd, stdout=subprocess.PIPE, bufsize=1, universal_newlines=True) as self.process:
            for line in self.process.stdout:
                logging.info(line[ : line.rfind('\n')])
                if 'CPU #' in line:
                    # find hash rate
                    line = line[ : line.rfind('H/s')]
                    hash_rate = _convert_to_float(line[line.rfind(', ') + 2 : ])
                    # find nof hashes
                    line = line[ : line.rfind('H, ')]
                    nof_hashes = _convert_to_float(line[line[ : -2].rfind(': ') + 2 : ])
                    # find core number
                    core_nr = int(line[line.rfind('#') + 1 : line.rfind(': ')])
                    # update
                    self.hash_sum[core_nr] += hash_rate * nof_hashes
                    self.nof_hashes[core_nr] += nof_hashes
                elif 'stratum_recv_line failed' in line:
                    if time() - self.last_fail_time > 20:
                        # too long ago so reset
                        self.fail_count = 1
                    else:
                        self.fail_count += 1
                    self.last_fail_time = time()


    def join(self):
        self.process.terminate()
        super().join()


'''
Assumes output is of the form '45.3 ' or '456.9 M'
'''
def _convert_to_float(output):
    hash_rate = float(output[ : output.rfind(' ')])
    if output[-1] == 'k':
        hash_rate *= 1000
    elif output[-1] == 'M':
        hash_rate *= 1000000
    elif output[-1] == 'G':
        hash_rate *= 1000000000
    elif output[-1] != ' ':
        raise(NotImplementedError('The following unit is not yet supported: ' + output[-1] + ' or there is something wrong with the output: ' + output))
    return hash_rate


def nicehash_multialgo_info():
    """Retrieves pay rates and connection ports for every algorithm from the NiceHash API."""
    response = urllib.request.urlopen('https://api.nicehash.com/api?method=simplemultialgo.info',
                                      None, NICEHASH_TIMEOUT)
    query = json.loads(response.read().decode('ascii'))
    paying = {}
    ports = {}
    for algorithm in query['result']['simplemultialgo']:
        name = algorithm['name']
        paying[name] = float(algorithm['paying'])
        ports[name] = int(algorithm['port'])
    return paying, ports

'''
Compute the expected revenue for each algorithm.

For algorithms that haven't been used before or that haven't been used in the past 24h the hash rate is increased by 20%.
This is to increase the likelyhood that an almost as profitable algorithm is selected so that the hash rates will be updated to the actual hash rate.
'''
def nicehash_mbtc_per_day(benchmarks, paying):
    """Calculates the BTC/day amount for every algorithm.
    device -- excavator device id for benchmarks
    paying -- algorithm pay information from NiceHash
    """
    revenue = {}
    for algorithm in benchmarks:
        # ignore revenue if the algorithm fails a lot
        if 'last_fail_time' in benchmarks[algorithm] and time() - benchmarks[algorithm]['last_fail_time'] < 60 * 60:
            revenue[algorithm] = 0
            continue

        # compute expected revenue
        revenue[algorithm] = paying[algorithm] * benchmarks[algorithm]['hash_rate'] * (24*60*60) * 1e-11

        # increase revenue by 20% if the algortihm hasn't been updated ever or if it has been more than 24h
        if 'last_updated' not in benchmarks[algorithm]:
            revenue[algorithm] *= 1.2
        elif time() - benchmarks[algorithm]['last_updated'] > PROFIT_INCREASE_TIME:
            nof_days_since_update = (time() - benchmarks[algorithm]['last_updated']) / PROFIT_INCREASE_TIME
            revenue_multiplier = 1 + nof_days_since_update * 2 / 100
            revenue[algorithm] *= min(1.2, revenue_multiplier)

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
    cpuminer_thread = None

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
            if cpuminer_thread != None:
                # Update hash rate if enough accepted hases have been seen
                if np.min(cpuminer_thread.nof_hashes) > NOF_HASHES_BEFORE_UPDATE:
                    benchmarks[running_algorithm]['hash_rate'] = np.sum(cpuminer_thread.hash_sum / cpuminer_thread.nof_hashes)
                    benchmarks[running_algorithm]['last_updated'] = time()
                    json.dump(benchmarks, open(BENCHMARKS_FILE, 'w'))
                    logging.info('UPDATED HASH RATE OF ' + running_algorithm + ' TO: ' + str(benchmarks[running_algorithm]['hash_rate']))
                # Remove payrate if the algorithm is not working
                if cpuminer_thread.fail_count > 5 and time() - cpuminer_thread.last_fail_time < 60:
                    payrates[running_algorithm] = 0
                    benchmarks[running_algorithm]['last_fail_time'] = cpuminer_thread.last_fail_time
                    json.dump(benchmarks, open(BENCHMARKS_FILE, 'w'))
                    logging.error(running_algorithm + ' FAILS MORE THAN ALLOWED SO IGNORING IT FOR NOW!')

            # Compute payout and get best algorithm
            payrates = nicehash_mbtc_per_day(benchmarks, paying)
            best_algorithm = max(payrates.keys(), key=lambda algo: payrates[algo])

            # Switch algorithm if it's worth while
            if running_algorithm == None or running_algorithm != best_algorithm and \
                (payrates[running_algorithm] == 0 or payrates[best_algorithm]/payrates[running_algorithm] >= 1.0 + PROFIT_SWITCH_THRESHOLD):

                # kill previous miner
                if cpuminer_thread != None:
                    cpuminer_thread.join()
                    logging.info('killed process running ' + running_algorithm)

                # start miner
                logging.info('starting mining using ' + best_algorithm + ' using ' + str(benchmarks[best_algorithm]['nof_threads']) + ' threads')
                cpuminer_thread = MinerThread(['./cpuminer', '-u', WALLET + '.' + WORKER, '-p', 'x',
                    '-o', 'stratum+tcp://' + best_algorithm + '.' + REGION + '.' + 'nicehash.com:' + str(ports[best_algorithm]),
                    '-a', best_algorithm, '-t', str(benchmarks[best_algorithm]['nof_threads'])], benchmarks[best_algorithm]['nof_threads'])
                cpuminer_thread.start()
                running_algorithm = best_algorithm

            if (np.sum(cpuminer_thread.nof_hashes) > 0) :
                logging.info('Current average hashrate is %f H/s' % np.sum(cpuminer_thread.hash_sum / cpuminer_thread.nof_hashes))
            logging.info(running_algorithm + ' is currently expected to generate %f mBTC/day or %f mBTC/month'
                         % (payrates[running_algorithm], payrates[running_algorithm] * 365 / 12))
        sleep(UPDATE_INTERVAL)

if __name__ == '__main__':
    if len(sys.argv) > 0:
        WALLET = sys.argv[1]
    if len(sys.argv) > 1:
        WORKER = sys.argv[2]
    main()