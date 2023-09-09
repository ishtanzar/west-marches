import logging


def get_logger(obj):
    return logging.getLogger(obj.__module__ + '.' + type(obj).__name__)

