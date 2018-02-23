"""
Celery tasks
"""
from typing import List, Dict, NoReturn
import uuid
from pathlib import Path

from app.celery import celery_app

from aws_searcher import searcher, config, mws_api


@celery_app.task
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


@celery_app.task
def get_asins_from_amazon_search_page(category: str,
                                      search_terms: str,
                                      page_number: int) -> List['str']:
    """
    Get a list of ASINs from amazon search pages, must know specific page numbers else
    returns empty list

    Args:
        category: The Amazon search category (e.g. Sports & Outdoors)
        search_terms: Search terms used as those user was searching page
        page_number: Page number of search result pagination (Out of range results in empty list)

    Returns:
        List of ASINs or empty list if page_number is not in range
    """
    soup = searcher.get_amazon_search_result(category, search_terms, page_number)
    return searcher.collect_target_pages_from_search_response(soup)


@celery_app.task
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

