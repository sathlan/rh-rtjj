from .check import Config
from .check import Check


def main():
    config = Config()
    return Check(config).run()
