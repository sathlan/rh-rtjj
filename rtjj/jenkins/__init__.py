from urllib.parse import urlparse
import datetime
import functools
import os
import re
from time import sleep
from pathlib import Path

import jenkins

os.environ['REQUESTS_CA_BUNDLE'] = '/etc/pki/tls/cert.pem'


class BuildInfo(object):
    def __init__(self, start='', desc='', url='', status=None, failure_stage=None):
        # failure is ignore, but enable to pipe the result of history
        # into the check command.
        self.start = start
        self.desc = desc
        self.url = url
        self.purl = urlparse(url)
        self.server_url = f"{self.purl.scheme}://{self.purl.netloc}"
        self.server = jenkins.Jenkins(self.server_url)

        self._status = status

    @functools.cached_property
    def build(self):
        self.build = self.server.get_build_info(
            self.job_name,
            self.number)
        return self.build

    @functools.cached_property
    def job_name(self):
        return self.parse_job_name(self.purl.path)

    @functools.cached_property
    def number(self):
        return self.parse_job_number(self.purl.path)

    @functools.cached_property
    def status(self):
        if self._status is None:
            self._status = self.build['result']
            if self.build['building']:
                self._status = 'RUNNING'
        return self._status

    @functools.cached_property
    def stages(self):
        self.stages = self.server.get_build_stages(
            self.job_name,
            self.number)['stages']
        return self.stages

    @functools.cached_property
    def failure_stage(self):
        current_stage = None

        if self.status == 'FAILURE' or self.status == 'RUNNING':
            current_stage = 'Not_started'
            for stage in self.stages:
                if stage['status'] == 'FAILED':
                    return stage['name']
                else:
                    current_stage = stage['name']
        return current_stage

    @staticmethod
    def parse_job_name(path):
        job_name = ''
        match = re.search(r'/\d+/?$', path)
        if match:
            m_name = re.match(r'^(?:.*/)?([^/]+)/?$',
                              str(Path(path).parent))
            job_name = m_name.group(1)
        else:
            m_name = re.match(r'^(?:.*/)?([^/]+)/?$', path)
            job_name = m_name.group(1)
        return job_name

    @staticmethod
    def parse_job_number(path):
        match = re.search(r'^.*/(\d+)/?$', path)
        if match:
            return int(match.group(1))
        else:
            return None

    @property
    def history(self):
        builds_hist = []
        builds = self.server.get_job_info(self.job_name)['builds']
        for build in builds:
            url = build['url']
            job_name = self.parse_job_name(url)
            number = self.parse_job_number(url)
            old_build = self.server.get_build_info(
                job_name,
                number)
            result = old_build['result']
            if old_build['building']:
                result = 'RUNNING'
            failure_stage = ''
            if result == 'FAILURE' or result == 'RUNNING':
                stages = self.server.get_build_stages(
                    job_name,
                    number)['stages']
                failure_stage = 'Not_started'
                for stage in stages:
                    if stage['status'] == 'FAILED':
                        failure_stage = stage['name']
                        break

            builds_hist.append({
                'url': url,
                'date': datetime.datetime.fromtimestamp(int(
                    old_build['timestamp']/1000)),
                'name': job_name,
                'number': number,
                'status': result,
                'failure_stage': failure_stage
            })

        return builds_hist

    def __str__(self):
        return(f"{self.start}, {self.desc}," +
               f"{self.server_url}, {self.status}, {self.server}")


class BuildNew(object):
    def __init__(self, server, job, parametrized=True, auth={}, params={}):
        self.job = job
        self.params = params
        if not self.params and parametrized:
            self.params = {'force': 'parametrized_build'}
        self.auth = auth
        self.server = jenkins.Jenkins(server, **auth)

    def trigger(self):
        queue_nbr = self.server.build_job(self.job, self.params)
        build = {}
        attempt = 0
        while 'executable' not in build:
            build = self.server.get_queue_item(queue_nbr)
            if attempt > 30:
                break
            sleep(2)
            attempt += 1
        if 'executable' not in build:
            return 'Unknow build for {job} on {server}'
        else:
            return build['executable']['url']


class JobsInfo(object):
    def __init__(self, view=None, pattern=None, url=''):
        os.environ['REQUESTS_CA_BUNDLE'] = '/etc/pki/tls/cert.pem'
        self.view = view
        self.pattern = pattern
        self.url = url
        self.purl = urlparse(url)
        self.server_url = f"{self.purl.scheme}://{self.purl.netloc}"
        self.server = jenkins.Jenkins(self.server_url)

    @functools.cached_property
    def jobs(self):
        jobs = []
        if self.view is not None:
            for job in self.server.get_jobs(view_name=self.view):
                jobs.append(job)
        if self.pattern is not None:
            for job in self.server.get_job_info_regex(self.pattern):
                jobs.append(job)
        return jobs

    @functools.cached_property
    def views(self):
        return self.server.get_views()
