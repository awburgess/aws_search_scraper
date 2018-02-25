"""
CLI access for AWS Searcher tooling
"""
import click
import threading
from queue import Queue
from functools import partial

from app import tasks
from aws_searcher import config


@click.command()
@click.option('--category', help="Amazon Search Category")
@click.option('--terms', help='Search terms')
@click.option('--market', default=config.MARKETPLACE_IDS['US'], help='Region Marketplace ID')
def run(category, terms, market):
    """
    Public Access Point

    """
    first_page_dict = tasks.get_first_page(category, terms)

    asin_queue = Queue()
    processed_queue = Queue()
    for asin in first_page_dict['asins']:
        asin_queue.put(asin)

    page_queue = Queue()
    pages = list(range(2, first_page_dict['last_page_number'] + 1))
    for page in pages:
        page_queue.put({'category': category, 'terms': terms, 'page_number': page})

    for thread_number in range(4):
        worker = threading.Thread(target=tasks.page_worker, args=(page_queue,
                                                                  asin_queue,
                                                                  processed_queue,))
        worker.setDaemon(True)
        worker.start()

    page_queue.join()

    for thread_number in range(4):
        worker = threading.Thread(target=tasks.api_worker, args=(asin_queue,
                                                                 processed_queue,))



