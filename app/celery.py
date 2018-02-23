"""
Celery app file
"""
from celery import Celery

celery_app = Celery('aws_searcher',
                    broker='amqp://guest@localhost:5672',
                    backend='amqp://guest@localhost:5672',
                    include=['app.tasks'])


