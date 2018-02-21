"""
Unit tests for searcher.py
"""

import pytest
import requests_mock

import aws_searcher.searcher as searcher


@pytest.fixture
def _soup_fixture() -> searcher.BeautifulSoup:
    """
    Pytest fixture for fake Amazon soup

    Returns:
        BeautifulSoup object
    """
    html = """<html><body><a class='s-access-detail-page' href='/dp/tacos/'></body</html>"""
    return searcher.BeautifulSoup(html, 'lxml')


@pytest.fixture
def _amazon_detail_page() -> searcher.BeautifulSoup:
    """
    Pytest fixture for creating BeautifulSoup object that uses saved Amazon product
    detail page

    Returns:
        BeautifulSoup object
    """
    dummy_file = searcher.Path(__file__).parent / 'resources' / 'aws_searcher_test_product.htm'
    with dummy_file.open() as infile:
        dummy_soup = searcher.BeautifulSoup(infile.read(), 'lxml')
    return dummy_soup


@pytest.fixture
def _amazon_detail_page_with_asins() -> searcher.BeautifulSoup:
    """
    Pytest fixture for creating BeautifulSoup object that uses saved
    Amazon product detail page

    Returns:
        BeautifulSoup object
    """
    dummy_file = searcher.Path(__file__).parent / 'resources' / 'test_page_with_asins.htm'
    with dummy_file.open() as infile:
        dummy_soup = searcher.BeautifulSoup(infile.read(), 'lxml')
    return dummy_soup


def test_get_amazon_search_result():
    """
    Test that _get_amazon_search_results works as expected

    """
    with requests_mock.mock() as m:
        m.get('https://www.amazon.com/s/ref=nb_sb_noss_1?'
              'url=search-alias=sporting&page=1&field-keywords=oakley',
              text="<div id='test'>Wieners!</div>")

        soup = searcher.get_amazon_search_result('Sports & Outdoors', 'Oakley')

        assert soup.find('div', {'id': 'test'}).text == 'Wieners!'

    with requests_mock.mock() as m:
        m.get('https://www.amazon.com/s/ref=src_pg_16?'
              'url=search-alias=sporting&page=16&field-keywords=oakley',
              text="<div id='test'>Wieners!</div>")

        soup = searcher.get_amazon_search_result('Sports & Outdoors', 'Oakley', 16)

        assert soup.find('div', {'id': 'test'}).text == 'Wieners!'


def test_collect_target_pages_from_search_response(_soup_fixture):
    """
    Test that _collect_target_pages_from_search_response works

    Args:
        _soup_fixture: Dummy BeautifulSoup object

    """
    urls = searcher.collect_target_pages_from_search_response(_soup_fixture)

    assert urls['tacos'] == 'https://www.amazon.com/dp/tacos'


def test_parse_product_page(_amazon_detail_page):
    """
    Test that _parse_product_page works

    """
    asin_dict = {'B075CYFMMT': 'https://www.amazon.com/dp/B075CYFMMT'}

    product_data = searcher.parse_product_page_details(asin_dict, _amazon_detail_page)

    assert product_data['asin'] == 'B075CYFMMT'
    assert product_data['brand'] == 'Oakley'
    assert product_data['price'] == '$203.00'
    assert product_data['sellers'] == ['A24JA0AG016EJ8']
    assert product_data['product_name'] == 'Oakley Mens Flak 2.0 Asian Fit Polarized ' \
                                           'Sunglasses, Matte Black/Prizm Jade,OS'


def test_scan_detail_page_for_asin(_amazon_detail_page_with_asins):
    """
    Test that _scan_detail_page_for_asin

    """
    extra_asins = searcher.scan_detail_page_for_asin(_amazon_detail_page_with_asins)
    expected_asins = ['B00G7NKJF0', 'B00G7NKKW2', 'B00G7NKMZ2', 'B00G7NKLRQ']
    assert sorted(
        list(extra_asins.values())) == sorted([searcher.urljoin(searcher.config.AMAZON_BASE_URL,
                                                               'dp/' + asin)
                                               for asin in expected_asins])


def test_get_pagination():
    """
    Test get_pagination

    """
    test_page = searcher.Path(__file__).parent / 'resources' / 'oakley_landing_page.htm'
    with test_page.open() as infile:
        soup = searcher.BeautifulSoup(infile.read(), 'lxml')

    page_number = searcher.get_pagination(soup) == 79


def test_serialize_to_csv(tmpdir):
    """
    Test serialize_to_csv

    """
    file = searcher.Path(str(tmpdir.join('dummy.csv')))

    data = [{'name': 'Aaron', 'age': '38'},
            {'name': 'Michelle', 'age': '32'}]

    searcher.serialize_to_csv(data, file)

    with file.open() as infile:
        reader = searcher.csv.DictReader(infile)
        assert reader.fieldnames == ['name', 'age']

        for count, line in enumerate(reader):
            assert line == data[count]
