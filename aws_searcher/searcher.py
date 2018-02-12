"""
Functions for submitting a search request to Amazon, getting the response and
parsing each result page for Product Name, Brand Name, AISN and Price
"""
from pathlib import Path
import re
from urllib.parse import urljoin, unquote
from multiprocessing.dummy import Pool, Queue
from typing import Union, NoReturn, List

import requests
from bs4 import BeautifulSoup

import aws_searcher.config as config


def _get_amazon_search_result(category: str,
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

    r = requests.get(url, headers={'user-agent': config.USER_AGENT})
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


def _collect_target_pages_from_search_response(soup: BeautifulSoup) -> dict:
    """
    Collects all product urls and returns as list

    Args:
        soup: BeautifulSoup Object representing search result page

    Returns:
        Dictionary with ASIN as key and url as value

    """
    urls = [_parse_asin_link(a['href']) for a in soup.find_all('a', class_='s-access-detail-page')]
    return {url.replace('/dp/', ''): urljoin(config.AMAZON_BASE_URL, url)
            for url in urls}


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


def parse_product_page_details(asin_dictionary: dict, page: BeautifulSoup) -> dict:
    """
    Parse the desired details from a given page

    Args:
        asin_dictionary: Dictionary with ASIN as keys and amazon url as value
        page: BeautifulSoup object representing product page

    Returns:
        Dictionary with Product Name, Brand, ASIN, Price, Seller Name
    """
    return {'asin': list(asin_dictionary.keys())[0],
            'brand': _extract_brand(page),
            'price': _extract_price(page),
            'sellers': _extract_sellers(page),
            'product_name': _extract_product_name(page)}


def _scan_detail_page_for_asin(soup: BeautifulSoup) -> List[str]:
    """
    Scan a detail page for more ASINs

    Args:
        soup: BeautifulSoup page for detail page

    Returns:
        List of ASINs found on page (if any)
    """
    return re.findall(r'(?<=data-dp-url="/dp/).+?(?=/)', str(soup))


