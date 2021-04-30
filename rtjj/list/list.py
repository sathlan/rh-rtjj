import argparse
import configparser
import csv
import functools
import re
import sys
from pathlib import Path
from urllib.parse import urljoin, urlparse

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
        parser.add_argument(
            "--conf",
            default=Path('~/.config/rtjj/conf.ini').expanduser()
        )
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

    def build_jobs_from_conf(self, entry):
        config = configparser.ConfigParser()
        config.optionxform = str
        config_file = Path(self.config.conf).expanduser()
        config.read(config_file)
        if entry not in config:
            raise(Exception("Cannot find {entry} in {config_file}."))
        urls_config = config[entry]['urls']
        server = ''
        if 'server' in config[entry]:
            server_entry = config[entry]['server']
            if server_entry in config:
                server = config[server_entry]['server_url']
        urls = []
        for url in urls_config.splitlines(False):
            urls.append(url)
        job_url = urlparse(urls[-1])
        if job_url.scheme != '':
            server = f"{job_url.scheme}://{job_url.netloc}"
        jobs = {}
        for url in urls:
            purl = urlparse(url)
            jobs[purl.path] = urljoin(server, purl.path)
        return jobs

    @functools.cached_property
    def jobs(self):
        jobs = {}
        if 'list' in self.config.view:
            for view in self.viewer(url=self.config.server).views:
                jobs[view['name']] = view['url']
            return jobs
        if self.config.entry is not None:
            return self.build_jobs_from_conf(self.config.entry)
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
        builds = self.builder(url=url).history(self.config.history_length)
        results = []
        desc = ''
        if self.config.entry is not None:
            desc = self.config.entry
        for build in builds:
            results.append({
                'start': build['date'],
                'desc': desc,
                'url': build['url'],
                'status': build['status'],
                'failure_stage': build['failure_stage'],
            })
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
