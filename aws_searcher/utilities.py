"""
Utilities for app
"""
import logging
import requests


def get_public_ip_address() -> str:
    """
    Utility to get public IP address

    Returns:
        Your machine's public IP address
    """
    json_ip = requests.get('https://jsonip.com/')
    if not json_ip.ok:
        logging.warning("Unable to reach jsonip.com, Public IP Unknown")
        return '127.0.0.1'
    return json_ip.json()['ip']


