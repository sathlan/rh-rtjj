import pytest
from collections import namedtuple

from rtjj.check import Check, Config


@pytest.mark.parametrize('config',
                         [Config(['tests/fixtures/jobs_list.csv'])])
def test_check_results(config, mocker):
    jenkins_results = [
        {'desc': '',
         'failure_stage': None,
         'start': '2021-04-15T19:48:11.598711',
         'status': 'ABORTED',
         'url': 'http://staging-jenkins2-qe-playground.usersys.redhat.com/job/DFG-upgrades-updates-13-from-zHA-ipv4/55/'},
        {'desc': '',
         'failure_stage': None,
         'start': '2021-04-15T19:48:11.598836',
         'status': 'ABORTED',
         'url': 'http://staging-jenkins2-qe-playground.usersys.redhat.com/job/DFG-upgrades-updates-13-from-zomposable-ipv6/37/'},
    ]
    jenkins_return_objs = []
    # Turn the dict into an object.
    for results in jenkins_results:
        jenkins_return_objs.append(namedtuple(
            'Jenkins',
            results.keys())(*results.values()))
    checker = mocker.MagicMock()
    checker.side_effect = jenkins_return_objs
    one_job = Check(config, checker)
    assert one_job.results == jenkins_results
