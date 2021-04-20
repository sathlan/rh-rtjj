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
        parser.add_argument("--history", action='store_true')
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

    def build_history(self, build, result):
        history = build.history
        cpt = 0
        while cpt < 10:
            if cpt < len(history):
                history_str = f"{history[cpt]['number']}|{history[cpt]['date']}|{history[cpt]['status']}|{history[cpt]['failure_stage']}"
                result[f'history_{cpt}'] = history_str
                self.fieldnames.append(f'history_{cpt}')
                cpt += 1
            else:
                break

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
