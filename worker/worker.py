import urllib.request
from bs4 import BeautifulSoup

import pika
import sys

connection = pika.BlockingConnection(
		pika.ConnectionParameters(host='rabbitmq'))
channel = connection.channel()

send_connection = pika.BlockingConnection(
		pika.ConnectionParameters(host='rabbitmq'))
send_channel = send_connection.channel()

def parse(link):
	res =  link
	try:
		page = urllib.request.urlopen(link)
		soup = BeautifulSoup(page, 'html.parser')
		ind = 0
		for link in soup.findAll("a"):
			tmp = link.get("href")
			if (tmp) and (tmp[0] == '/'):
				res += '#https://en.wikipedia.org'
				res += tmp
				ind = 1
	except:
		pass
	return res

channel.queue_declare(queue='urls', durable=True)

send_channel.confirm_delivery()
send_channel.queue_declare(queue='parsed', durable=True)

def callback(ch, method, properties, body):
	print('Callback', flush=True)
	link = body.decode()
	ch.basic_ack(delivery_tag=method.delivery_tag)
	res = parse(link)
	while (True):
		try:
			send_channel.basic_publish(
				exchange='',
				routing_key='parsed',
				body=res,
				properties=pika.BasicProperties(
					delivery_mode=2,    
				),
				mandatory=True)
			break
		except:
			#Confirmation
			pass

channel.basic_qos(prefetch_count=1)
channel.basic_consume(queue='urls', on_message_callback=callback)

channel.start_consuming()
