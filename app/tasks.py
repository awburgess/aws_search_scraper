"""
Celery tasks
"""
from typing import List, Dict, NoReturn
import uuid
from pathlib import Path
from queue import Queue
from aws_searcher import searcher, config, mws_api


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


def serialize_data(data: List[Dict[str, str]], directory: Path) -> NoReturn:
    """
    Serializes data to csv for one worker.  Pandas will later
    concatenate all csvs into one and load into database

    Args:
        data: List of dictionaries as rows.  Keys defined by config file
        directory: Path object referencing output directory

    Returns:
        No Return
    """
    unique_id = uuid.uuid4()
    full_write_path = directory / (str(unique_id) + '.csv')
    searcher.serialize_to_csv(data, full_write_path)


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
        asin_list = get_asins_from_amazon_search_page(**arg_dict)
        processed_q_as_list = list(processed_q.queue)
        for asin in asin_list:
            if asin not in processed_q_as_list:
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
            asins.append(asin_q.get())

        asin_data_dict = mws_api.acquire_mws_product_data(marketplace_id, asins)



