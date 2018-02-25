"""
Functions for accessing MWS API and handling responses
"""

from operator import getitem
from functools import reduce
from typing import List

from mws import Products

import aws_searcher.config as config


class TooManyASINS(Exception):  # pragma: no cover
    """
    Custom exception class for when there are more than 5 asins requested
    """
    pass


def _get_product_object() -> Products:  # pragma: no cover
    """
    Creates a MWS Product object from mws library

    Returns:
        Products object
    """
    return Products(access_key='AKIAJICBE76XQKHWUTLA', #os.getenv('MWS_ACCESS_KEY'),
                    secret_key='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', #os.getenv('MWS_SECRET_KEY'),
                    account_id='AQ5JN7IFU4T3S') # os.getenv('SELLER_ID'))


def _extract_values_by_target_keys(keys: List[str], json_response: dict) -> str:
    """
    Extract the values for specific keys

    Args:
        keys: list of string lists where they are the dict keys in order
        json_response: Response from MWS API

    Returns:
        Extracted Value
    """
    try:
        return reduce(getitem, keys, json_response)
    except KeyError:  # pragma: no cover
        return ''


def _extract_target_data(data: dict) -> dict:
    """
    Extract desired data as dict

    Args:
        data: Product data from MWS, parsed JSON as python dict

    Returns:
        Dictionary for serialization
    """
    return {key: _extract_values_by_target_keys(config.TARGET_KEYS[key], data)
            for key in config.TARGET_KEYS}


def _extract_asin_from_relationshp(relationship_dict: dict, key: str) -> List[str]:
    """
    Extract list of ASINs (either parent or children)

    Args:
        relationship_dict: Relationship dict from json response
        relationship: 'VariationParent' or 'VariationChild'

    Returns:
        List of ASINs
    """
    if key == 'VariationParent':
        return [_extract_values_by_target_keys(config.RELATIONSHIP_KEYS['related_asin'], relationship_dict[key])]
    return [_extract_values_by_target_keys(config.RELATIONSHIP_KEYS['related_asin'], item)
            for item in relationship_dict[key]]


def acquire_mws_product_data(marketplace: str, asins: List[str]) -> dict:  # pragma: no cover
    """
    Get the details as set by the config file's TARGET_KEYS to extract and label from
    MWS API.  Also returns relationship ASINs as key to add to any given list or queue

    Args:
        marketplace: MWS Marketplace ID
        asins: Single or list of asins to query (Max length of 5)

    Returns:
        Dictionary of with three parent keys, "target_values", "raw_data" and "related_asins".  The
        "target_values" key will house a list of dictionaries as rows.  The related asins will
        be a list of asin strings to possibly add to Queue
    """
    if len(asins) > 5:
        raise TooManyASINS("Maximum 5 ASINs in any one request")

    products_obj = _get_product_object()
    product_data = products_obj.get_matching_product(marketplace, asins).parsed

    if isinstance(product_data, dict):
        product_data = [product_data]

    rows = [_extract_target_data(data) for data in product_data]

    related_asins = []

    for data in product_data:
        row_dict = {}

        relationship_dict = data['Product']['Relationships']

        row_dict['asin'] = _extract_values_by_target_keys(config.TARGET_KEYS['asin'], data)

        try:
            relationship = list(relationship_dict.keys())[0]
            asins = _extract_asin_from_relationshp(relationship_dict,
                                                   list(relationship_dict.keys())[0])
        except IndexError:
            relationship = 'asexual'
            asins = []

        row_dict['relationship'] = relationship

        row_dict['related_asins'] = asins

    return {'target_values': rows,
            'raw_data': product_data,
            'related_asins': related_asins}


