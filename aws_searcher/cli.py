"""
CLI access for AWS Searcher tooling
"""
import click
import threading
from queue import Queue
from pathlib import Path
import logging

import pandas as pd

try:
    import config as config
    import tasks as tasks
    import models as models
except ImportError:
    import aws_searcher.config as config
    import aws_searcher.tasks as tasks
    import aws_searcher.models as models


@click.command()
@click.option('--category', help="Amazon Search Category")
@click.option('--terms', help='Search terms')
@click.option('--market', default=config.MARKETPLACE_IDS['US'], help='Region Marketplace ID')
def run(category, terms, market):
    """
    Public Access Point

    """
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

    log_path = this_job_dir / (str(job_id) + '.log')
    log_path.touch()
    logging.basicConfig(filename=log_path.as_posix(),
                        filemode='a',
                        level=logging.INFO,
                        format='%(asctime)s | %(threadName)s | %(levelname)s | %(message)s')

    output_name = '_'.join([category.lower(), terms.lower()])

    logging.info("Processing page 1")

    first_page_dict = tasks.get_first_page(category, terms)
    logging.info("Page processed, adding ASINs to queue")

    asin_queue = Queue()
    processed_queue = Queue()
    blocker_queue = Queue()

    for asin_group in tasks.grouper(5, first_page_dict['asins']):
        clean_group = tasks.clean_groups(asin_group)
        asin_queue.put(clean_group)

    page_queue = Queue()
    pages = list(range(2, first_page_dict['last_page_number'] + 1))
    for page in pages:
        page_queue.put({'category': category, 'search_terms': terms, 'page_number': page})

    for thread_number in range(4):
        worker = threading.Thread(target=tasks.page_worker, args=(page_queue,
                                                                  asin_queue))
        worker.setDaemon(True)
        worker.start()

    page_queue.join()

    for thread_number in range(4):
        worker = threading.Thread(target=tasks.api_worker, args=(asin_queue,
                                                                 processed_queue,
                                                                 blocker_queue,
                                                                 market,))
        worker.setDaemon(True)
        worker.start()

    asin_queue.join()

    logging.info("Collecting JSON data into one file")
    tasks.combine_json_files(output_name)

    logging.info("Collecting output data for db load and final output")
    all_data_files = pd.concat(pd.read_csv(f.as_posix()) for f in data_dir.glob('*.csv'))
    all_data_files['job'] = job_id

    all_relationship_files = pd.concat(pd.read_csv(f.as_posix()) for f in data_dir.glob('*.dat'))
    all_relationship_files['job'] = job_id

    all_attribute_files = pd.concat(pd.read_csv(f.as_posix()) for f in data_dir.glob('*.txt'))
    all_attribute_files['job'] = job_id

    tasks.remove_files(data_dir, 'csv')
    tasks.remove_files(data_dir, 'txt')
    tasks.remove_files(data_dir, 'dat')

    out_data_csv = this_job_dir / (output_name + '.csv')
    out_relationship_csv = this_job_dir / (output_name + '_relationships.csv')
    out_attributes_csv = this_job_dir / (output_name + '_attributes.csv')
    failed_asins_txt = this_job_dir / (output_name + '_failed_asins.txt')

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

    failed_asins_list = list(blocker_queue.queue)
    if failed_asins_list:
        logging.warning("Serializing failed asins, total %d" % len(failed_asins_list))
        with failed_asins_txt.open('w') as outfile:
            outfile.write(','.join(failed_asins_list))
        logging.warning("Failed ASINs are failed")

    engine.execute("""UPDATE jobs SET status = 'Complete' WHERE id = {}""".format(job_id))
    engine.dispose()

    logging.info("Run complete")

if __name__ == '__main__':
    run()
