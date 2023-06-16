import json

import pendulum
from kafka import KafkaProducer
from kafka.errors import KafkaError

from .config import config


def print_command(command: str) -> None:
    local_now = pendulum.now('local')
    print(f'{local_now} | {command}')


def kafka_send(command: str) -> None:
    # TODO оптимизировать
    if not config.kafka:
        print('Настройки Kafka не указаны.')
        return

    producer = KafkaProducer(
        bootstrap_servers=config.kafka.server,
        value_serializer=lambda m: json.dumps(m).encode('utf-8'),
        acks=0,  # 1,'all' вынести в настройки
    )

    future = producer.send(config.kafka.topic, {'command': command})
    try:
        record_metadata = future.get(timeout=10)  # вынести в настройки
    except KafkaError:
        print('Kafka error')
    else:
        print(record_metadata.offset)
