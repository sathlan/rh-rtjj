from urllib.parse import urlparse
import datetime
import functools
import os
import re
from time import sleep
from pathlib import Path

import jenkins


class BuildInfo(object):
    def __init__(self, start='', desc='', url='', status=None):
        os.environ['REQUESTS_CA_BUNDLE'] = '/etc/pki/tls/cert.pem'
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
        match = re.search(r'/\d+/?', self.purl.path)
        if match:
            self.job_name = Path(self.purl.path).parent.stem
        else:
            self.job_name = Path(self.purl.path).stem
        return self.job_name

    @functools.cached_property
    def number(self):
        self.number = int(Path(self.purl.path).stem)
        return self.number

    @functools.cached_property
    def status(self):
        if self._status is None:
            self._status = self.build['result']
        return self._status

    @functools.cached_property
    def stages(self):
        self.stages = self.server.get_build_stages(
            self.job_name,
            self.number)['stages']
        return self.stages

    def has_failed(self):
        return self.status == 'FAILURE'

    @functools.cached_property
    def failure_stage(self):
        stage = None
        if self.has_failed():
            for stage in self.stages:
                if stage['status'] == 'FAILED':
                    return stage['name']
        return stage

    @property
    def history(self):
        builds_hist = []
        builds = self.server.get_job_info(self.job_name)['builds']
        for build in builds:
            url = build['url']
            job_name = Path(url).parent.stem
            number = int(Path(url).stem)
            old_build = self.server.get_build_info(
                job_name,
                number)
            result = old_build['result']
            stages = self.server.get_build_stages(
                job_name,
                number)['stages']

            failure_stage = ''
            if result == 'FAILURE':
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

    @property
    def jobs(self):
        jobs = []
        if self.view is not None:
            for job in self.server.get_jobs(view_name=self.view):
                jobs.append(job)
        if self.pattern is not None:
            for job in self.server.get_job_info_regex(self.pattern):
                jobs.append(job)
        return jobs
