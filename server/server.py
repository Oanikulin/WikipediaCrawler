import pika
import time
import os
import time

from concurrent import futures
import grpc
import asyncio
import threading

import messages_pb2
import messages_pb2_grpc

processed_lock = threading.Lock()
processed = []
connection = pika.BlockingConnection(
        pika.ConnectionParameters(host='rabbitmq'))
receive_channel = connection.channel()
receive_channel.queue_declare(queue='parsed', durable=True)

class WikiCrawlerServicer(messages_pb2_grpc.WikiCrawlerServicer):

    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.count = 0

    def AddToQueue(self, messg):
        while (True):
            try:
                self.channel.basic_publish(
                    exchange='',
                    routing_key='urls',
                    body=messg,
                    properties=pika.BasicProperties(
                        delivery_mode=2,    
                    ),
                    mandatory=True)
                break
            except Exception as inst:
                #Confirmation
                print(type(inst), flush=True)
                print(inst, flush=True)
                print('Failed', flush=True)
                time.sleep(1)
                pass

    def ParseRMQMessage(self, msg):
        urls = list(msg.split('#'))
        d = self.parent[urls[0]][1] + 1
        for i in range(1, len(urls)):
            if urls[i] not in self.parent:
                self.parent[urls[i]] = [urls[0], d + 1]
                self.next_urls.append(urls[i])

    def RestorePath(self, url):
        res = []
        while self.parent[url][1] != 0:
            res.append(url)
            url = self.parent[url][0]
        res = res[::-1]
        return res

    def Crawl(self, request, context):
        global processed
        with self.lock:
            self.connection = pika.BlockingConnection(
                pika.ConnectionParameters(host='rabbitmq'))
            self.channel = self.connection.channel()
            self.channel.confirm_delivery()
            self.channel.queue_declare(queue='urls', durable=True)
            self.current_urls = [request.fromp]
            self.next_urls = []
            self.parent = dict()
            self.parent[request.fromp] = ["", 0]
            while (True):
                processed = []
                print('New length iteration', flush=True)
                self.count = len(self.current_urls)
                for url in self.current_urls:
                    self.AddToQueue(url)
                #dumb spinlock
                print('Starting spinlock', flush=True)
                while (True):
                    with processed_lock:
                        length = len(processed)
                    print('Waiting, processed ', length, ' out of ', self.count, flush=True)
                    if (length != self.count):
                        time.sleep(1)
                    else:
                        break
                for urls in processed:
                    self.ParseRMQMessage(urls)
                for url in self.next_urls:
                    if (url == request.to):
                        res = self.RestorePath(url)
                        for url in res:
                            yield messages_pb2.Result(path=url, length=len(res))
                        return
                self.current_urls = self.next_urls[:]
                self.next_urls = []



def start_consumer():

    def callback(ch, method, properties, body):
        global processed
        data = body.decode()
        with processed_lock:
            processed.append(data)
        ch.basic_ack(delivery_tag=method.delivery_tag)
    
    receive_channel.basic_qos(prefetch_count=1)
    receive_channel.basic_consume(queue='parsed', on_message_callback=callback)
    receive_channel.start_consuming()

def serve():
    print('Staring server', flush=True)
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    port = os.environ.get('MESSENGER_SERVER_PORT', 51075)
    messages_pb2_grpc.add_WikiCrawlerServicer_to_server(
        WikiCrawlerServicer(), server)
    server.add_insecure_port('0.0.0.0:' + str(port))
    server.start()
    
    print("Starting consumer", flush=True)
    consumer_thread = threading.Thread(target=start_consumer)
    consumer_thread.start()
    print("Serving forerver", flush=True)
    server.wait_for_termination()

serve()


