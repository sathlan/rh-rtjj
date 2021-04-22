import pytest
import rtjj.jenkins as Jenkins
from collections import namedtuple

from rtjj.list import List, Config


def test_list_view(mocker, capsys):
    jenkins_results = [
        {
            'fullname': 'foobar1',
            'url': 'https://myjenkins.com/foobar1'
        },
        {
            'fullname': 'foobar2',
            'url': 'https://myjenkins.com/foobar2'
        }]
    config = Config(['--view', 'foo/bar',
                     '--server', 'https://myJenkins.com/'])

    viewer = Jenkins.JobsInfo
    viewer.jobs = mocker.PropertyMock(return_value=jenkins_results)
    List(config, viewer=viewer).main()
    view = capsys.readouterr()
    assert view.out == 'https://myjenkins.com/foobar1\n' + \
        'https://myjenkins.com/foobar2\n'


def test_list_named(mocker, capsys):
    jenkins_results = [
        {
            'fullname': 'foobar1',
            'url': 'https://myjenkins.com/foobar1'
        },
        {
            'fullname': 'foobar2',
            'url': 'https://myjenkins.com/foobar2'
        }]
    config = Config(['--view', 'foo/bar',
                     '--server', 'https://myJenkins.com/',
                     '--named', 'foobar'])

    viewer = Jenkins.JobsInfo
    viewer.jobs = mocker.PropertyMock(return_value=jenkins_results)
    List(config, viewer=viewer).main()
    view = capsys.readouterr()
    assert view.out == '[foobar]\nurls = https://myjenkins.com/foobar1\n' + \
        '       https://myjenkins.com/foobar2\n'


def test_list_history(mocker, capsys):
    config = Config(['--view', 'foo/bar',
                     '--server', 'https://myJenkins.com/',
                     '--history'])
    jenkins_view_results = [
        {
            'fullname': 'foobar1',
            'url': 'https://myjenkins.com/foobar1'
        }]
    jenkins_build_results = [
        {
            'date': '2021',
            'url': 'https://myjenkins.com/foobar1/8',
            'status': 'SUCCESS',
            'failure_stage': '',
        },
        {
            'date': '2021',
            'url': 'https://myjenkins.com/foobar1/9',
            'status': 'FAILURE',
            'failure_stage': 'stage1',
        }]
    viewer = Jenkins.JobsInfo
    viewer.jobs = mocker.PropertyMock(return_value=jenkins_view_results)
    builder = Jenkins.BuildInfo
    builder.history = mocker.PropertyMock(return_value=jenkins_build_results)
    List(config, viewer=viewer, builder=builder).main()
    view = capsys.readouterr()
    output = 'start,desc,url,status,failure_stage\r\n' + \
        '2021,,https://myjenkins.com/foobar1/8,SUCCESS,\r\n' + \
        '2021,,https://myjenkins.com/foobar1/9,FAILURE,stage1\r\n'
    assert view.out == output
