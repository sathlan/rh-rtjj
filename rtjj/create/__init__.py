from .create import Config
from .create import Create


def main():
    config = Config()
    return Create(config).csv()
