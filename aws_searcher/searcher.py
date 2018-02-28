"""
Functions for submitting a search request to Amazon, getting the response and
parsing each result page for Product Name, Brand Name, AISN and Price
"""
import random
from pathlib import Path
import csv
import re
from urllib.parse import urljoin, unquote
from typing import Union, NoReturn, List
import time

import requests
from bs4 import BeautifulSoup

import config
from logger import logger

import mws_api as api

LOGGER = logger('aws_scanner')


def get_amazon_search_result(category: str,
                             search_terms: str,
                             page: int = 1) -> Union[BeautifulSoup, NoReturn]:
    """
    Form the appropriate url for search

    Args:
        category: Amazon category (E.g. Books, Apps & Games, etc)
        search_terms: User provided search terms

    Keyword Args:
        page: page number to reach.  Assume first page if not indicated

    Returns:
        BeautifulSoup object from returned page
    """
    reference_global = config.AMAZON_INITIAL_REFERENCE \
        if page == 1 else config.PAGINATION_BASED_REFERENCE

    search_category = config.CATEGORIES_DICT[category]

    url = config.AMAZON_SEARCH_URL_TEMPLATE.format(reference=reference_global,
                                                   category=search_category,
                                                   search=search_terms,
                                                   page_number=page)

    r = requests.get(url, headers=config.REQUEST_HEADERS)
    if not r.ok:
        return
    return BeautifulSoup(r.text, 'lxml')


def _parse_asin_link(url: str) -> str:
    """
    Grab the /dp/<ASIN> pattern from collected urls to avoid carrying over session and
    cookie based info

    Args:
        url: String representing the target url

    Returns:
        A new url with a direct link to the product
    """
    return re.findall(r'/dp/.+?(?=/)', unquote(url))[0]


def collect_target_pages_from_search_response(soup: BeautifulSoup) -> List[str]:
    """
    Collects all product urls and returns as list

    Args:
        soup: BeautifulSoup Object representing search result page

    Returns:
        List of ASINs

    """
    urls = [_parse_asin_link(a['href']) for a in soup.find_all('a', class_='s-access-detail-page')]
    return [url.replace('/dp/', '') for url in urls]


# TODO: May need to derive from sellers (may not be directly present on page even)
# TODO: Also condition for used (do new & used)
# TODO: Capture shipping & tax if present
def _extract_price(soup: BeautifulSoup) -> str:
    """
    Extract the price from the amazon page

    Args:
        soup: BeautifulSoup object representing the page

    Returns:
        String representation of sale price
    """
    return soup.find('span', {'id': 'priceblock_ourprice'}).text


def _extract_brand(soup: BeautifulSoup) -> str:
    """
    Extract brand name (Or byline if not by authentic seller)

    Args:
        soup: BeautifulSoup object representing the page

    Returns:
        String representation of the brand
    """
    image_brand_group = soup.find('div', {'id': 'brandByline_feature_div'})
    brand_group = soup.find('a', {'id': 'bylineInfo'})
    if brand_group:
        return brand_group.text.strip()
    return re.findall(r'(?<=bin=).+$', image_brand_group.find('a')['href'])[0]


# TODO: Parent title, need specific name (child title)
def _extract_product_name(soup: BeautifulSoup) -> str:
    """
    Extract the product name (e.g. Roger's Big Ol' Dildos)

    Args:
        soup: BeautifulSoup object for page

    Returns:
        String representing product name
    """
    return soup.find('span', {'id': 'productTitle'}).text.strip()


def _extract_sellers(soup: BeautifulSoup) -> List[str]:
    """
    Extract the names of sellers

    Args:
        soup: BeautifulSoup object representing page

    Returns:
        List of seller names
    """
    merchant_info = soup.find('div', {'id': 'merchant-info'})
    seller_ids = re.findall(r'(?<=seller=).+?(?=[\'"])', str(merchant_info))
    amazon_check = re.search(r'Fulfilled by Amazon', str(merchant_info))
    if amazon_check:
        seller_ids.append('Amazon')
    return seller_ids


def parse_product_page_details(asin_dictionary: dict, page: BeautifulSoup,
                               stringify: bool = False) -> dict:
    """
    Parse the desired details from a given page

    Args:
        asin_dictionary: Dictionary with ASIN as keys and amazon url as value
        page: BeautifulSoup object representing product page

    Keyword Args:
        stringify: Convert all values to string if true

    Returns:
        Dictionary with Product Name, Brand, ASIN, Price, Seller Name
    """
    sellers = _extract_sellers(page)
    return {'asin': list(asin_dictionary.keys())[0],
            'brand': _extract_brand(page),
            'price': _extract_price(page),
            'sellers': '|'.join(sellers) if stringify else sellers,
            'product_name': _extract_product_name(page)}


def get_product_page(url: str) -> BeautifulSoup:
    """
    Request product page using get request and return as BeautifulSoup object

    Args:
        url: String representation of product url

    Returns:
        BeautifulSoup object
    """
    return BeautifulSoup(requests.get(url, headers=config.REQUEST_HEADERS).text, 'lxml')


def scan_detail_page_for_asin(soup: BeautifulSoup) -> dict:
    """
    Scan a detail page for more ASINs

    Args:
        soup: BeautifulSoup page for detail page

    Returns:
        List of amazon urls for the given ASINs
    """
    all_asins = re.findall(r'(?<=data-dp-url=./dp/).+?(?=/)', str(soup))
    return {asin: urljoin(config.AMAZON_BASE_URL, 'dp/' + asin) for asin in all_asins}


def timeout(floor: int = 2, ceiling: int = 6) -> NoReturn:  # pragma: no cover
    """
    Invoke time.sleep at randomly timed intervals

    Keyword Args:
        floor: Minimum time to wait
        ceiling: Maximum time to wait

    """
    time.sleep(random.randint(floor, ceiling))


def serialize_to_csv(data: List[dict], file_path: Path,
                     declared_headers: List[str] = None,
                     write_mode: str = 'w') -> NoReturn:
    """
    Dump list of dicts to csv

    Args:
        data: List of dictionaries as rows
        file_path: Path reference to file write location

    Keyword Args:
        declared_headers: Declare headers to write
        write_mode: Indicate whether this should be a single write or append

    """
    headers = list(set(list(row.keys()) for row in data))
    with file_path.open(write_mode) as outfile:
        headers = headers if not declared_headers else declared_headers
        writer = csv.DictWriter(outfile, headers)
        if write_mode == 'w':
            writer.writeheader()
        writer.writerows(data)


def get_pagination(soup: BeautifulSoup) -> int:
    """
    Parse Amazon search result page and find last page number of results so
    that we know what to feed into the Queue

    Args:
        soup: BeautifulSoup object

    Returns:
        Integer representation of the last page number of result

    """
    return int(soup.find('span', {'class': 'pagnDisabled'}).text)

