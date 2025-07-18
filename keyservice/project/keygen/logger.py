import logging


logging.basicConfig(
    format="%(asctime)s %(levelname)-8s %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:S",
)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)