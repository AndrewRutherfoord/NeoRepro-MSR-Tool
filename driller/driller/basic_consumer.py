import json
import pika
import time
from pika.exchange_type import ExchangeType

connection = pika.BlockingConnection(
    pika.ConnectionParameters(host='localhost'))
channel = connection.channel()

channel.exchange_declare(exchange='test', exchange_type=ExchangeType.fanout)
channel.queue_declare(queue='task_queue', durable=True)
print(' [*] Waiting for messages. To exit press CTRL+C')


def callback(ch, method, properties, body):
    task = json.loads(body.decode())
    print(f" [x] Received {task}")
    # time.sleep(task.get("task_time"))
    time.sleep(3)
    print(" [x] Done")
    ch.basic_ack(delivery_tag=method.delivery_tag)


channel.basic_qos(prefetch_count=1)
channel.basic_consume(queue='task_queue', on_message_callback=callback)

channel.start_consuming()