import logging
import sys


def setup_logger(name='my_logger', level=logging.INFO):
    """Logger Setup.

    Sample Usage:
    logger = setup_logger()
    logger.info("Logging to stdout only.")

    Args:
        name (str, optional): _description_. Defaults to 'my_logger'.
        level (_type_, optional): _description_. Defaults to logging.INFO.

    Returns:
        _type_: _description_
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if logger.hasHandlers():
        return logger

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)
    return logger


if __name__ == "__main__":
    pass
