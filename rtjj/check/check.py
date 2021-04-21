import argparse
import csv
import functools
import sys

import rtjj.jenkins as Jenkins


class Config(object):
    def __init__(self, args=None):
        parser = argparse.ArgumentParser(
            "Check Jenkins jobs status based on a csv file.")

        parser.add_argument("csv_builds", nargs='?',
                            type=argparse.FileType('r'),
                            default=sys.stdin)
        parser.add_argument("csv_results", nargs='?',
                            type=argparse.FileType('w'),
                            default=sys.stdout)
        if args is None:
            args = sys.argv[1:]
        self.args = parser.parse_args(args)


class Check(object):
    def __init__(self, config, checker=None):
        self.config = config.args
        self.checker = checker
        if checker is None:
            self.checker = Jenkins.BuildInfo
        self.initial_fieldnames = ['start', 'desc', 'url', 'status', 'failure_stage']
        self.fieldnames = ['start', 'desc', 'url', 'status', 'failure_stage']

    @functools.cached_property
    def results(self):
        csv_builds = csv.DictReader(self.config.csv_builds)
        self.results = []
        for build_entry in csv_builds:
            build = self.checker(**build_entry)
            result = {}
            for field in self.initial_fieldnames:
                result[field] = getattr(build, field)
            if self.config.history:
                self.build_history(build, result)
            self.results.append(result)
        return self.results

    def csv(self):
        results = self.results
        csv_output = csv.DictWriter(
            self.config.csv_results,
            fieldnames=self.fieldnames)
        csv_output.writeheader()
        for result in results:
            csv_output.writerow(result)

    def run(self):
        self.csv()
