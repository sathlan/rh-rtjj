import argparse
import configparser
import csv
import datetime as dt
import functools
import sys

import rtjj.jenkins as Jenkins


class Config(object):
    def __init__(self, args=None):
        parser = argparse.ArgumentParser(
            "Create a Jenkins job and output the url of the triggered job.")

        parser.add_argument("--job")
        parser.add_argument("--jobs")
        parser.add_argument("--param", action='append', default=[])
        parser.add_argument("--server")
        parser.add_argument("--auth", default=None)
        parser.add_argument("--conf", default=None)
        parser.add_argument("--no-header", action='store_true')
        parser.add_argument("--desc", default='')
        if args is None:
            args = sys.argv[1:]
        self.args = parser.parse_args(args)


class Create(object):
    def __init__(self, config, builder=None):
        self.config = config.args
        self.builder = builder
        if builder is None:
            self.builder = Jenkins.BuildNew
        self.fmt_time = "%Y-%m-%dT%H:%M:%S.%f%z"
        self.fieldnames = ['start', 'desc', 'url']
        self.urls = []

    def jobs(self):
        self.jobs = []
        if self.config.conf is None:
            raise(Exception("You need to pass the configuration to use jobs"))
        config = configparser.ConfigParser()
        config.read(self.config.conf)
        if 'jobs' not in config:
            raise(Exception("You need to define a [jobs] section in the conf"))
        if self.config.jobs not in config['jobs']:
            raise(Exception(f"{self.config.jobs} doesn't exist in the configuration"))
        for job in config['jobs'][self.config.jobs].splitlines(False):
            self.jobs.append(job)

        return self.jobs

    @functools.cached_property
    def params(self):
        params = {}
        if self.config.conf is not None:
            config = configparser.ConfigParser()
            config.read(self.config.conf)
            for section in ['DEFAULT', self.config.server]:
                if section in config:
                    params.update(config[section])
        for cli_param in self.config.param:
            (key, value) = cli_param.split('=')
            params[key] = value
        return params

    def auth(self):
        auth = {}
        auth_file = None
        if 'auth' in self.params:
            auth_file = self.params.pop('auth')
        if self.config.auth is not None:
            auth_file = self.config.auth
        if auth_file is not None:
            with open(auth_file, 'r') as perm:
                for line in perm:
                    (username, password) = line.strip().split(':')
                    auth['username'] = username
                    auth['password'] = password
        return auth

    @property
    def server(self):
        server = self.config.server
        if 'url' in self.params:
            server = self.params.pop('url')
        return server

    def trigger(self):
        jobs = []
        if self.config.jobs is None:
            jobs.append(self.config.job)
        else:
            jobs = self.jobs()

        for job in jobs:
            url = self.builder(server=self.server,
                               job=job,
                               auth=self.auth(),
                               params=self.params).trigger()
            self.urls.append(url)

        if len(self.urls) == 1:
            return self.urls[0]
        else:
            return self.urls

    def csv(self):
        self.trigger()
        csv_output = csv.DictWriter(
            sys.stdout,
            fieldnames=self.fieldnames)
        if not self.config.no_header:
            csv_output.writeheader()
        for url in self.urls:
            csv_output.writerow({
                'start': dt.datetime.now().strftime(self.fmt_time),
                'desc': self.config.desc,
                'url': url,
            })
