"""
CLI access for AWS Searcher tooling
"""
import click
import threading
from queue import Queue
from pathlib import Path
import logging

import pandas as pd

import config
import tasks
import models


@click.command()
@click.option('--category', help="Amazon Search Category")
@click.option('--terms', help='Search terms')
@click.option('--market', default=config.MARKETPLACE_IDS['US'], help='Region Marketplace ID')
def run(category, terms, market):
    """
    Public Access Point

    """
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s | %(threadName)s | %(levelname)s | %(message)s')

    data_dir = Path.home() / config.DATA_DIRECTORY
    db_dir = Path.home() / config.DB_DIRECTORY
    jobs_dir = Path.home() / config.JOBS_DIRECTORY

    db_dir.mkdir(parents=True, exist_ok=True)
    data_dir.mkdir(parents=True, exist_ok=True)
    jobs_dir.mkdir(parents=True, exist_ok=True)

    logging.info('Confirming db exists and creating job entry')
    engine = models.get_engine(db_dir / 'amazon.db')
    models.BASE.metadata.create_all(bind=engine)

    job_record = engine.execute(models.Jobs.__table__.insert().values(category=category,
                                                                      terms=terms))
    job_id = job_record.inserted_primary_key[0]

    this_job_dir = jobs_dir / str(job_id)

    this_job_dir.mkdir(parents=True, exist_ok=True)

    output_name = '_'.join([category.lower(), terms.lower()])

    logging.info("Processing page 1")

    first_page_dict = tasks.get_first_page(category, terms)
    logging.info("Page processed, adding ASINs to queue")

    asin_queue = Queue()
    processed_queue = Queue()
    for asin_group in tasks.grouper(5, first_page_dict['asins']):
        asin_queue.put(asin_group)

    page_queue = Queue()
    pages = list(range(2, first_page_dict['last_page_number'] + 1))
    for page in pages:
        page_queue.put({'category': category, 'search_terms': terms, 'page_number': page})

    for thread_number in range(4):
        worker = threading.Thread(target=tasks.page_worker, args=(page_queue,
                                                                  asin_queue,
                                                                  processed_queue,))
        worker.setDaemon(True)
        worker.start()

    page_queue.join()

    for thread_number in range(4):
        worker = threading.Thread(target=tasks.api_worker, args=(asin_queue,
                                                                 processed_queue,
                                                                 market,))
        worker.setDaemon(True)
        worker.start()

    asin_queue.join()

    logging.info("Collecting JSON data into one file")
    tasks.combine_json_files(output_name)

    logging.info("Collecting output data for db load and final output")
    all_data_files = pd.concat(pd.read_csv(f.as_posix()) for f in data_dir.glob('*.csv'))

    all_relationship_files = pd.concat(pd.read_csv(f.as_posix()) for f in data_dir.glob('*.dat'))

    all_attribute_files = pd.concat(pd.read_csv(f.as_posix()) for f in data_dir.glob('*.txt'))

    tasks.remove_files(data_dir, 'csv')
    tasks.remove_files(data_dir, 'txt')
    tasks.remove_files(data_dir, 'dat')

    out_data_csv = this_job_dir / (output_name + '.csv')
    out_relationship_csv = this_job_dir / (output_name + '_relationships.csv')
    out_attributes_csv = this_job_dir / (output_name + '_attributes.csv')

    logging.info("Saving %s" % out_data_csv)
    all_data_files.to_csv(out_data_csv.as_posix(), index=False)

    logging.info("Inserting annotated data into database")
    all_data_files.to_sql('annotated_data_' + str(job_id),
                          con=engine, if_exists='append', index=False)

    logging.info("Saving %s" % out_relationship_csv)
    all_relationship_files.to_csv(out_relationship_csv.as_posix(), index=False)
    logging.info("Inserting relationships into database")
    all_relationship_files.to_sql('relationships', con=engine, if_exists='append', index=False)

    logging.info("Saving %s" % out_attributes_csv)
    all_attribute_files.to_csv(out_attributes_csv.as_posix(), index=False)
    logging.info("Inserting attributes into database")
    all_attribute_files.to_sql('attributes_' + str(job_id), con=engine, if_exists='append',
                               index=False)

    logging.info("Run complete")


if __name__ == '__main__':
    run()