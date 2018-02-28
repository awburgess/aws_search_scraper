"""
Celery tasks
"""
from typing import List, Dict, NoReturn
import uuid
from pathlib import Path
from queue import Queue
import json
import logging

import searcher, config, mws_api


def get_asin_data(asin_list: List[str], marketplace_id: str) -> Dict[str, list]:
    """
    Call the Amazon MWS api and return a dictionary with 'target_values',
    'related_asins' as keys, where 'target_values' are a list of
    data rows as single level dictionaries representing response values as
    defined in the config file

    Args:
        asin_list: List of ASINs
        marketplace_id: Amazon marketplace id (e.g. codes for US, EU, etc)

    Returns:
        Dictionary with 'target_values' as list of rows for serialization and
        'related_asins' to send to the Queue

    """
    return mws_api.acquire_mws_product_data(marketplace_id, asin_list)


def get_asins_from_amazon_search_page(category: str,
                                      search_terms: str,
                                      page_number: int) -> List[str]:
    """
    Get a list of ASINs from amazon search pages, must know specific page numbers else
    returns empty list

    Args:
        category: The Amazon search category (e.g. Sports & Outdoors)
        search_terms: Search terms used as though user was searching page
        page_number: Page number of search result pagination (Out of range results in empty list)

    Returns:
        List of ASINs or empty list if page_number is not in range
    """
    soup = searcher.get_amazon_search_result(category, search_terms, page_number)
    searcher.timeout()
    return searcher.collect_target_pages_from_search_response(soup)


def serialize_data_to_csv(data: List[Dict[str, str]],
                          directory: Path,
                          extension: str = 'csv') -> NoReturn:
    """
    Serializes data to csv for one worker.  Pandas will later
    concatenate all csvs into one and load into database

    Args:
        data: List of dictionaries as rows.  Keys defined by config file
        directory: Path object referencing output directory

    Keyword Args:
        extension: file extension to use, csv by default

    Returns:
        No Return
    """
    unique_id = uuid.uuid4()
    full_write_path = directory / (str(unique_id) + '.' + extension)
    searcher.serialize_to_csv(data, full_write_path)


def serialize_data_to_json(data: List[Dict[str, str]], directory: Path) -> NoReturn:
    """
    Serialize data to json for one worker.  Non-threaded operation will concat

    Args:
        data: List of dictionaries representing JSON response from MWS
        directory: Directory path to write to

    """
    unique_id = uuid.uuid4()
    full_write_path = directory / (str(unique_id) + '.json')
    with full_write_path.open('w') as outfile:
        json.dump(data, outfile)


def combine_json_files(name: str):
    """
    Collect all output json files, combine into one list, re-serialize to single file

    Args:
        name: String representation of JSON file name

    """
    json_files_path = Path.home() / config.DATA_DIRECTORY
    output_json_file = json_files_path / (name + '.json')
    json_files = json_files_path.glob('*.json')
    all_json_data = []
    for file in json_files:
        with file.open() as infile:
            all_json_data = all_json_data + json.load(infile)
        file.unlink()

    with output_json_file.open('w') as outfile:
        json.dump(all_json_data, outfile)


def flatten_item_attributes(json_dict) -> Dict[str, str]:
    """
    Flatten item attributes

    Args:
        json_dict: Attribute JSON Dict

    Returns:
        Dictionary with flattened json
    """
    out = {}

    def flatten(x, name=''):
        if isinstance(x, dict):
            for a in x:
                flatten(x[a], name + a + '_')
        elif isinstance(x, list):
            i = 0
            for a in x:
                flatten(a, name + str(i) + '_')
                i += 1
        else:
            out[name[:-1].replace('_value', '')] = x

    flatten(json_dict)
    return out


def extract_relationships_from_json(asin: str, relationship_dict: dict) -> List[Dict[str, str]]:
    """
    Extract group of dicts as rows with asin and it's parent (if applicable)

    Args:
        relationship_dict: Dictionary with relatinships as parent or list of children

    Returns:
        List of dictionary with asin,  child or parent, and parent (empty string if asin is parent)

    """
    relationship = list(relationship_dict.keys())[0]
    related_asins_list = mws_api._extract_asin_from_relationshp(relationship_dict, relationship)
    if relationship == 'VariationParent':
        return [{'asin': asin, 'relationship': relationship, 'parent': related_asins_list[0]}]
    else:
        return [{'asin': related_asins, 'relationship': relationship, 'parent': asin}
                for related_asins in related_asins_list]


def get_first_page(category: str, search_terms: str) -> dict:
    """
    Get the first search result page and return initial ASINs and
    the pagination limit

    Args:
        category: The Amazon Search category (e.g. Sports & Outdoors)
        search_terms: Search terms to use

    Returns:
        A dict with 'asins' & 'last_page_number' as keys where
        'asins' value is a list of ASINs and 'last_page_number' value
        is an integer representing the last page
    """
    soup = searcher.get_amazon_search_result(category, search_terms, 1)
    last_page = searcher.get_pagination(soup)
    asins = searcher.collect_target_pages_from_search_response(soup)
    return {'asins': asins, 'last_page_number': last_page}


def remove_files(data_dir: Path, extension: str) -> NoReturn:
    """
    Remove iterative files used to combine into final result

    Args:
        data_dir: Data directory where output was written
        extension: extension to target for removal

    """
    for file in data_dir.glob('*.' +  extension):
        file.unlink()


def page_worker(page_q: Queue, asin_q: Queue, processed_q: Queue):
    """
    Worker function for threading out asins from website pages

    Args:
        page_q: Queue with arg dicts for get_asins_from_amazon_search_page
        asin_q: Queue with ASINs to be processed on MWS API
        processed_q: ASINs that have already been processed

    """
    while True:
        arg_dict = page_q.get()

        logging.info("Processing page: %d" % arg_dict['page_number'])

        asin_list = get_asins_from_amazon_search_page(**arg_dict)

        logging.info("Page processed, adding ASINs to queue")

        for asin in asin_list:
            if asin not in processed_q.queue:
                asin_q.put(asin)
        page_q.task_done()


def api_worker(asin_q: Queue, processed_q: Queue, marketplace_id: str):
    """
    Worker function for threading out api calls

    Args:
        asin_q: Queue with ASINs to be processed on MWS API
        processed_q: ASINs that have already been processed
        marketplace_id: String represeentation

    """
    while True:
        asins = []
        for x in range(5):
            if asin_q.empty():
                break
            queue_asin = asin_q.get()
            if queue_asin not in processed_q.queue:
                asins.append(queue_asin)

        if not asins:
            continue

        asins = list(set(asins))

        log_asins = ', '.join(asins)

        logging.info("Processing ASINs: %s" % log_asins)

        try:
            asin_data_dict = mws_api.acquire_mws_product_data(marketplace_id, asins)
        except:
            logging.warning("API is throttling")
            logging.warning("Pausing for a minute")
            for asin in asins:
                asin_q.put(asin)
            searcher.time.sleep(60)
            continue

        searcher.timeout()

        logging.info("Serializing Raw Data for %s" % log_asins)
        serialize_data_to_json(asin_data_dict['raw_data'], Path.home() / config.DATA_DIRECTORY)

        logging.info("Save complete")

        attributes = []
        relationships = []
        for data in asin_data_dict['raw_data']:
            attributes.append(flatten_item_attributes(
                data['Product']['AttributeSets']['ItemAttributes']
            ))
            relationships.append(extract_relationships_from_json(data['ASIN']['value'],
                                                                 data['Product']['Relationships']))

        write_path = Path.home() / config.DATA_DIRECTORY

        logging.info('Serializing Raw JSON Response')
        serialize_data_to_json(asin_data_dict['raw_data'], write_path)
        logging.info('Saved Raw JSON')

        logging.info('Serializing Two Dimensional Representation of Attributes')
        serialize_data_to_csv(attributes, write_path, extension='txt')
        logging.info('Saved Two Dimensional Representation of Attributes')

        logging.info('Serializing Relationships')
        serialize_data_to_csv(relationships, write_path, extension='dat')
        logging.info('Saved Relationships')

        logging.info('Serializing target values to csv')
        serialize_data_to_csv(asin_data_dict['target_values'], write_path)
        logging.info('Saved target values')

        for asin in asins:
            processed_q.put(asin, block=False)

        for related_dict in relationships:
            if related_dict['asin'] not in processed_q.queue:
                processed_q.put(related_dict['asin'], block=False)

        asin_q.task_done()