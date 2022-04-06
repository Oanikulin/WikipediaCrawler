FROM python:3.8

COPY . .

RUN pip install -r requirements.txt

CMD ["bash", "-c", "while ! curl -s rabbitmq:15672 > /dev/null; do echo waiting for rabbitmq; sleep 3; done; python server.py"]