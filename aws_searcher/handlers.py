"""
App Views
"""
import subprocess
import shlex
import logging
from pathlib import Path
from flask import render_template

from aws_searcher import app, socketio
from aws_searcher.models import get_engine, query_jobs
import aws_searcher.config as config
from aws_searcher.utilities import get_public_ip_address

_ENGINE = get_engine(Path.home() / (config.DB_DIRECTORY + '/' + 'amazon.db'))

_CURRENT_IP = ''

LOGGER = logging.basicConfig(level=logging.INFO,
                             format='%(asctime)s | %(threadName)s | %(levelname)s | %(message)s')


@app.route('/')
def home():
    """
    Get main page

    Returns:
        Renders index html page
    """
    return render_template('index.html', categories=config.CATEGORIES_DICT)


@socketio.on('connected')
def connector():
    """
    Handler for initial connection, queries jobs

    """
    _CURRENT_IP = get_public_ip_address()
    logging.info('Current IP: %s' % _CURRENT_IP)
    jobs = query_jobs(_ENGINE)
    headers = [{'title': column} for column in ['id', 'category', 'terms', 'run_date']]
    socketio.emit('jobs', {'data': {'headers': headers, 'rows': jobs}}, json=True)

