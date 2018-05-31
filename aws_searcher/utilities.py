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


def replace_none_in_dict(json_obj: dict) -> dict:
    """
    Replace the Nones before they become null in JavaScript

    Args:
        json_obj: Dictionary representing what will be the JSON object

    Returns:
        A new dictionary with no Nones and hence no nulls
    """
    new_dict = {}
    for key, value in json_obj.items():
        if value is None:
            value = ''
        new_dict[key] = value
    return new_dict
