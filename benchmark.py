import multiprocessing
import subprocess
import json
import logging


def run(nicehash_algorithms):
	logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s',
                        level=logging.INFO)

	logging.info('BENCHMARKING...')

	## Read the list of algorithms the miner supports ##

	f = open('algorithms.txt')
	miner_algorithms = f.readlines()

	for i in range(len(miner_algorithms)):
	    algorithm = miner_algorithms[i]
	    end = algorithm.find('\n')
	    if algorithm.find(' ') > 0:
	        end = min(end, algorithm.find(' '))
	    if end > 0:
	        miner_algorithms[i] = algorithm[: end]


	## Do the actual benchmark and find the optimal number of threads

	benchmarked_algorithms = {}
	max_nof_threads = multiprocessing.cpu_count()
	benchmark_str = 'Benchmark: '
	for algorithm in nicehash_algorithms:
	    if algorithm in miner_algorithms:
	        bash_command = './cpuminer --benchmark --time-limit=13 -a ' + algorithm
	        optimal_nof_threads = 0
	        optimal_hash_rate = 0
	        logging.info('Benchmarking ' + algorithm + ' ...')
	        for t in range(1, max_nof_threads + 1):
	            logging.info('with ' + str(t) + ' thread(s)')
	            output = subprocess.check_output(['bash', '-c', bash_command + ' -t ' + str(t)]).decode("utf-8")
	            output = output[output.rfind(benchmark_str) + len(benchmark_str) : ]
	            output = output[ : output.find('H/s')]
	            hash_rate = float(output[ : output.rfind(' ')])
	            if output[-1] == 'k':
	                hash_rate *= 1000
	            elif output[-1] == 'M':
	                hash_rate *= 1000000
	            elif output[-1] == 'G':
	                hash_rate *= 1000000000
	            elif output[-1] != ' ':
	                raise(NotImplementedError('The following unit is not yet supported: ' + output[-1] + ' or there is something wrong with the output: ' + output))
	            if hash_rate > optimal_hash_rate:
	                optimal_hash_rate = hash_rate
	                optimal_nof_threads = t
	        if optimal_hash_rate > 0:
	            benchmarked_algorithms[algorithm] = {
	                'hash_rate' : optimal_hash_rate,
	                'nof_threads' : optimal_nof_threads
	            }
	            logging.info('Benchmarked ' + algorithm + ' with selected parameters: ' + str(benchmarked_algorithms[algorithm]))
	        else:
	            logging.info('algorithm ' + algorithm + ' not added because the hash rate was 0.')

	json.dump(benchmarked_algorithms, open('benchmarks.json', 'w'))


	## logging.info the results

	logging.info('Final results: ' + str(benchmarked_algorithms))
	logging.info('Done! The results are stored in benchmarks.json')


if __name__ == '__main__':
	import cpuminer_driver
	paying, ports = cpuminer_driver.nicehash_multialgo_info()
	run(paying.keys())