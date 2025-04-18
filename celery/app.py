import os
from celery import Celery

BACKEND  = os.getenv('CELERY_RESULT_BACKEND', 'rpc://')
BROKER = os.getenv('CELERY_BROKER_URL', 'amqp://admin:admin@localhost:5672//')





app = Celery(
    'gazprom_case',
    broker=BROKER, 
    backend=BACKEND,                                          
)



app.conf.update(
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    task_acks_late=True,
)

import tasks