"""
Unit tests for mws api
"""
from pathlib import Path
import json

import pytest

import aws_searcher.mws_api as api
import aws_searcher.config as config


@pytest.fixture
def target_data() -> dict:
    """
    Fixture that provides API data

    """
    file = Path(__file__).parent / 'resources' / 'product_api_response.json'

    with file.open() as infile:
        data = json.load(infile)

    return data


@pytest.fixture
def relationship_dicts() -> dict:
    """
    Fixture that provides a VariantParent and VariantChildren values

    """
    parent = {
        'VariationParent': {
            'Identifiers': {
                'MarketplaceASIN': {
                    'ASIN': {
                        'value': 'TickleStick'
                    }
                }
            }
        }

    }

    children = {
        'VariationChild': [{
            'Identifiers': {
                'MarketplaceASIN': {
                    'ASIN': {
                        'value': 'TickleStick'
                    }
                }
            }
        },
            {
                'Identifiers': {
                    'MarketplaceASIN': {
                        'ASIN': {
                            'value': 'Geni'
                        }
                    }
                }
            }]

    }

    return {'parent': parent, 'children': children}


def test_extract_target_data(target_data):
    """
    Test extract_target_path

    Args:
        target_data: Pytest fixture for api response data

    """
    data = {
        'asin': 'B00D69E120',
        'brand': 'Oakley',
        'product': "Oakley Holbrook Sunglasses - Oakley Men's Lifestyle Rectangular Authentic Eyewear - Crystal Black/Violet Iridium / One Size Fits All",
        'price': '130.00', 'currency': 'USD'
    }

    result_data = api._extract_target_data(target_data)

    for key, item in data.items():
        assert result_data[key] == item


def test_extract_asin_from_relationship(relationship_dicts):
    """
    Test extract_asin_from_relationship

    """
    parent_result = api._extract_asin_from_relationship(relationship_dicts['parent'],
                                                       'VariationParent')

    children_result = api._extract_asin_from_relationship(relationship_dicts['children'],
                                                         'VariationChild')

    assert parent_result == ['TickleStick']

    assert sorted(children_result) == ['Geni', 'TickleStick']
