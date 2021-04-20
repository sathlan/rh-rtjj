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

        parser.add_argument("--view", action='append', default=[])
        parser.add_argument("--pattern", action='append', default=[])
        parser.add_argument("--exclude", action='append', default=[])
        parser.add_argument("--include", action='append', default=[])
        parser.add_argument("--entry")
        parser.add_argument("--conf")
        parser.add_argument("--server")
        if args is None:
            args = sys.argv[1:]
        self.args = parser.parse_args(args)

        if args is None:
            args = sys.argv[1:]
        self.args = parser.parse_args(args)


class List(object):
    def __init__(self, config, viewer=None):
        self.config = config.args
        self.viewer = viewer
        if viewer is None:
            self.viewer = Jenkins.JobsInfo

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

    def short(self):
        for name, url in self.jobs.items():
            print(f"{url}")
