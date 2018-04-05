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
from aws_searcher.utilities import get_public_ip_address, replace_none_in_dict

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
    return render_template('index.html',
                           markets=config.MARKETPLACE_IDS,
                           categories=config.CATEGORIES_DICT)


@socketio.on('connected')
def connector():
    """
    Handler for initial connection, queries jobs

    """
    _CURRENT_IP = get_public_ip_address()
    logging.info('Current IP: %s' % _CURRENT_IP)
    jobs = query_jobs(_ENGINE)
    socketio.emit('jobs', {'data': {'rows': jobs}}, json=True)


@socketio.on('jobUpdates')
def job_updates():
    jobs = query_jobs(_ENGINE)
    socketio.emit('jobCheck', {'data': {'rows': jobs}}, json=True)


@socketio.on('getJob')
def get_job(job_json):
    """
    Handler for getting details on job by request

    Args:
        job_json: JSON object job number

    """
    rows_query = config.ROWS_QUERY.format(job=job_json['job'])
    relationships_query = config.RELATIONSHIP_QUERY.format(job=job_json['job'])

    rows_result = _ENGINE.execute(rows_query).fetchall()

    rows_header = [col.replace('_', '').lower() for col in rows_result[0].keys()]
    rows_data = [replace_none_in_dict(dict(zip(rows_header, row.values())))
                 for row in rows_result]
    relationship_data = [relationship.values()
                         for relationship in _ENGINE.execute(relationships_query).fetchall()]
    relationship_headers = ['relationship', 'relative', 'asin', 'job']

    socketio.emit('jobResult', {'rows': rows_data,
                                'row_headers': rows_header,
                                'relationships': relationship_data,
                                'relationship_headers': relationship_headers}, json=True)


@socketio.on('submit')
def submit_job(data):
    """
    Handler for running mws search job

    Args:
        data: JSON data from message with category, terms and market

    """
    run_file = Path(__file__).parent / 'cli.py'
    run_command = config.CLI_RUN.format(cli_file=run_file.as_posix(),
                                        category=data['category'],
                                        terms=data['terms'],
                                        market=data['market'])
    subprocess.Popen(shlex.split(run_command))
