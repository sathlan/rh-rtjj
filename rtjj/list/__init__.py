from .list import Config
from .list import List


def main():
    config = Config()
    return List(config).short()
