from dataclasses import asdict
import json
import time
import pika
import uuid

from driller.config_driller import DrillConfig, apply_defaults
from driller.settings import config_logging
from driller.util import load_yaml, parse_config

logger = config_logging()

class DrillerClient(object):
    queue = "driller_queue"

    def __init__(self):
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(host="localhost")
        )

        self.channel = self.connection.channel()

        result = self.channel.queue_declare(queue="", exclusive=True)
        self.callback_queue = result.method.queue

        self.channel.basic_consume(
            queue=self.callback_queue,
            on_message_callback=self.on_response,
            auto_ack=True,
        )

        self.response = None
        self.corr_id = None

    def on_response(self, ch, method, props, body):
        if self.corr_id == props.correlation_id:
            self.response = body

    def call(self, task: DrillConfig):
        self.response = None
        self.corr_id = str(uuid.uuid4())
        self.channel.basic_publish(
            exchange="",
            routing_key="driller_queue",
            properties=pika.BasicProperties(
                reply_to=self.callback_queue,
                correlation_id=self.corr_id,
            ),
            body=task.to_json(),
        )
        while self.response is None:
            self.connection.process_data_events(time_limit=None)
        return self.response

def get_drill_configs(file) -> list[DrillConfig]:
    conf = load_yaml(file)
    neo, defaults, projects = parse_config(conf)
    
    configs = []
    for project in projects:
        p = apply_defaults(project, defaults=defaults)
        configs.append(DrillConfig(neo=neo, project=p))
    
    return configs


driller = DrillerClient()
configs = get_drill_configs("driller/configs/test.yaml")

for conf in configs:
    response = driller.call(conf)
    logger.info(response)
