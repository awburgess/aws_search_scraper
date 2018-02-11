"""
Functions for submitting a search request to Amazon, getting the response and
parsing each result page for Product Name, Brand Name, AISN and Price
"""
from pathlib import Path
from multiprocessing.dummy import Pool

import requests
from bs4 import BeautifulSoup

