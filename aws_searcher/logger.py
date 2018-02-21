"""
A quick and easy logger for all your needs
"""

import logging


def logger(logger_name: str) -> logging.Logger:  # pragma: no cover
    """
    Creates new instance of default logger

    Args:
        logger_name: Name for your logger

    Returns:
        Logger object configured to default
    """
    new_logger = logging.getLogger(logger_name)
    new_logger.setLevel(logging.INFO)

    streamhandler = logging.StreamHandler()
    streamhandler.setLevel(logging.INFO)

    formatter = logging.Formatter('%(asctime)s | %(name)s | %(levelname)s | %(message)s')
    streamhandler.setFormatter(formatter)

    new_logger.addHandler(streamhandler)

    return new_logger