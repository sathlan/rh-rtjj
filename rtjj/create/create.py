from urllib.parse import urlparse
from pathlib import Path
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

        parser.add_argument("--job", action='append', default=[])
        parser.add_argument("--server")
        parser.add_argument("--param", action='append', default=[])
        parser.add_argument("--auth", default=None)
        parser.add_argument("--jobs")
        parser.add_argument(
            "--conf",
            default=Path('~/.config/rtjj/conf.ini').expanduser()
        )
        parser.add_argument("--no-header", action='store_true')
        parser.add_argument("--desc", default=None)
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
        self._server = None
        self._jobs = []
        self.config_parser = configparser.ConfigParser()
        self.config_parser.optionxform = str
        self._auth_file = None

    @property
    def jobs(self):
        if self._jobs:
            return self._jobs
        jobs = []
        if self.config.job:
            self._jobs = self.config.job
            return self._jobs
        job_section = self.config.jobs
        if job_section is not None:
            if not Path(self.config.conf).exists():
                raise(Exception(
                    "Cannot find {self.config.conf} and 'jobs' was used."))
            config = self.config_parser
            config.read(Path(self.config.conf).expanduser())
            if job_section not in config:
                raise(Exception(
                    f"You need to define a [{job_section}] section in the conf"))
        return jobs

    @functools.cached_property
    def params(self):
        params = {}
        if self.config.conf is not None and len(self.config.job) == 0:
            config = self.config_parser
            config.read(self.config.conf)
            for section in ['DEFAULT', self.config.server, self.config.jobs]:
                if section is not None and section in config:
                    params.update(config[section])
            if 'urls' in params:
                for url in params['urls'].splitlines(False):
                    self._jobs.append(url)
                # Assume all jobs are on the same server.
                job_url = urlparse(self._jobs[-1])
                if job_url.scheme != '':
                    self._server = f"{self.purl.scheme}://{self.purl.netloc}"
                params.pop('urls')
            if 'server' in params:
                server_section = params.pop('server')
                if server_section in config:
                    params.update(config[server_section])
            # TODO: unused
            if 'alias' in params:
                params.pop('alias')
            if 'server_url' in params:
                self._server = params.pop('server_url')
            if 'auth' in params:
                self._auth_file = params.pop('auth')
        for cli_param in self.config.param:
            (key, value) = cli_param.split('=')
            params[key] = value
        return params

    @property
    def auth(self):
        auth_file = None
        if self._auth_file is not None:
            auth_file = self._auth_file
        # Command line wins
        if self.config.auth is not None:
            auth_file = self.config.auth
        auth = {}
        if auth_file is not None:
            with open(Path(auth_file).expanduser(), 'r') as perm:
                for line in perm:
                    (username, password) = line.strip().split(':')
                    auth['username'] = username
                    auth['password'] = password
        return auth

    @property
    def server(self):
        if self._server is None:
            server = None
            if self.config.server is not None:
                server = self.config.server
            else:
                raise(Exception("Cannot find the server url."))
            return server
        else:
            # Make sure to remove it anyway.
            if 'server_url' in self.params:
                server = self.params.pop('server_url')
            return self._server

    def trigger(self):
        params = self.params
        for job in self.jobs:
            url = self.builder(server=self.server,
                               job=job,
                               auth=self.auth,
                               params=params).trigger()
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
        desc = self.config.jobs
        if self.config.desc is not None:
            desc = self.config.desc
        for url in self.urls:
            csv_output.writerow({
                'start': dt.datetime.now().strftime(self.fmt_time),
                'desc': desc,
                'url': url,
            })
