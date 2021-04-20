import argparse
import sys

class MyFileType(argparse.FileType):
    def __call__(self, string):
        if string.endswith(".gz"):
            try:
                return gzip.open(
                    string,
                    self._mode,
                    self._bufsize,
                    self._encoding,
                    self._errors
                )
            except OSError as e:
                args = {'filename': string, 'error': e}
                message = ("can't open '%(filename)s': %(error)s")
                raise argparse.ArgumentTypeError(message % args)
        return super(MyFileType, self).__call__(string)


class Config(object):
    def __init__(self):
        parser = argparse.ArgumentParser(
            "Manipulate jenkins: create, check, show.")

        parser.add_argument("csv_jobs", nargs='?',
                            type=argparse.FileType('r'),
                            default=sys.stdin)

        parser.add_argument("--check")


        parser.add_argument("--create", nargs='?',
                            type=argparse.FileType('r'))

        parser.add_argument("--unixlog", nargs='?',
                            type=argparse.FileType('r'))

        parser.add_argument("-t", "--title")

        # TODO: currently broken, need subplots see https://plotly.com/python/table-subplots/
        # and https://stackoverflow.com/questions/64482262/how-to-add-a-table-next-a-plotly-express-chart-and-save-them-to-a-pdf
        parser.add_argument("-P", "--ping-table",
                            default=False,
                            action='store_true')

        self.args = parser.parse_args()


def main():
    all_confs = Config()
    config = all_confs.args
    print(f"{config}")
