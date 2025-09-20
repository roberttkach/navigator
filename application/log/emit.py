import logging

from ...domain.log.emit import jlog


def debug(logger, code, **fields):
    jlog(logger, logging.DEBUG, code, **fields)


def info(logger, code, **fields):
    jlog(logger, logging.INFO, code, **fields)


def warning(logger, code, **fields):
    jlog(logger, logging.WARNING, code, **fields)


def error(logger, code, **fields):
    jlog(logger, logging.ERROR, code, **fields)


__all__ = ["jlog", "debug", "info", "warning", "error"]
