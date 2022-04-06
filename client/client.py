import sys 
sys.path.append('..')

import time
import grpc
import messages_pb2
import messages_pb2_grpc

import os


if __name__ == '__main__':
	print('Staring client', flush=True)
	grpcServerAddr = os.environ.get('MESSENGER_SERVER_ADDR', 'crawler:51075')

	channel = grpc.insecure_channel(grpcServerAddr)

	stub = messages_pb2_grpc.WikiCrawlerStub(channel)

	while (True):
		try:
			print('Reading two links to wikipedia pages from environment variables FROM_URL and TO_URL:', flush=True)
			#some random links from default
			from_url = os.environ.get('FROM_URL', 'https://en.wikipedia.org/wiki/ABA_problem')
			to_url = os.environ.get('TO_URL', 'https://en.wikipedia.org/wiki/Completely_Fair_Scheduler')
			print('Starting the crawling', flush=True)
			received_path = stub.Crawl(messages_pb2.Task(fromp=from_url, to=to_url))
			length = 1
			print('First step is', from_url)
			for tmp in received_path:
				length += 1
				print('Next step is ', tmp.path, flush=True)
			print('Total length is ', length, flush=True)
			break
		except grpc.RpcError as e:
			print(e.details(), flush=True)
			print('Please, retry', flush=True)
			time.sleep(1)

	print('Path was found successfully', flush=True)