FROM python:3.8

COPY client/requirements.txt .
RUN pip install -r requirements.txt

COPY server/. .

COPY client/. .

CMD ["bash", "-c", "while ! curl -s rabbitmq:15672 > /dev/null; do echo waiting for rabbitmq; sleep 3; done; python client.py"]