import argparse
import csv
import functools
import re
import sys

import rtjj.jenkins as Jenkins


class Config(object):
    def __init__(self, args=None):
        parser = argparse.ArgumentParser(
            "List Jenkins jobs based on view or regexp.")

        parser.add_argument("--server")
        parser.add_argument("--view", action='append', default=[])
        parser.add_argument("--pattern", action='append', default=[])
        parser.add_argument("--named", default=None)
        parser.add_argument("--exclude", action='append', default=[])
        parser.add_argument("--include", action='append', default=[])
        parser.add_argument("--entry")
        parser.add_argument("--conf")
        parser.add_argument("--history", action='store_true')
        parser.add_argument("--history-length", default=10)
        parser.add_argument("output", nargs='?',
                            type=argparse.FileType('w'),
                            default=sys.stdout)
        if args is None:
            args = sys.argv[1:]
        self.args = parser.parse_args(args)

        if args is None:
            args = sys.argv[1:]
        self.args = parser.parse_args(args)


class List(object):
    def __init__(self, config, viewer=None, builder=None):
        self.config = config.args
        self.viewer = viewer
        self.builder = builder
        if viewer is None:
            self.viewer = Jenkins.JobsInfo
        if builder is None:
            self.builder = Jenkins.BuildInfo
        self.fieldnames = ['start', 'desc', 'url', 'status', 'failure_stage']

    def filter(self, direction, regexp, jobs):
        fjobs = {}
        for name, url in jobs.items():
            match = regexp.match(name)
            if match:
                if direction == 'include':
                    fjobs.update({name: url})
            else:
                if direction == 'exclude':
                    fjobs.update({name: url})
        return fjobs

    @functools.cached_property
    def jobs(self):
        jobs = {}

        for view in self.config.view:
            for job in self.viewer(view=view,
                                   url=self.config.server).jobs:
                jobs[job['fullname']] = job['url']
        for pattern in self.config.pattern:
            for job in self.viewer(pattern=pattern,
                                   url=self.config.server).jobs:
                jobs[job['fullName']] = job['url']
        for inc in self.config.include:
            jobs = self.filter('include', re.compile(inc), jobs)
        for exc in self.config.exclude:
            jobs = self.filter('exclude', re.compile(exc), jobs)
        return jobs

    def build_history(self, url):
        history = self.builder(url=url).history
        cpt = 0
        results = []
        while cpt < int(self.config.history_length):
            if cpt < len(history):
                results.append({
                    'start': history[cpt]['date'],
                    'desc': '',
                    'url': history[cpt]['url'],
                    'status': history[cpt]['status'],
                    'failure_stage': history[cpt]['failure_stage'],
                })
                cpt += 1
            else:
                break
        return results

    def my_print(self, msg):
        print(msg, file=self.config.output)

    def main(self):
        if not self.config.history:
            pad = ""
            for name, url in self.jobs.items():
                if self.config.named is not None:
                    if pad == "":
                        self.my_print(f"[{self.config.named}]")
                        self.my_print(f"urls = {url}")
                        pad = " " * len("urls = ")
                        continue
                self.my_print(f"{pad}{url}")
        else:
            csv_output = csv.DictWriter(
                self.config.output,
                fieldnames=self.fieldnames)
            csv_output.writeheader()
            for _, url in self.jobs.items():
                for result in self.build_history(url):
                    csv_output.writerow(result)
