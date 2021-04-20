from rtjj.create import Config
from rtjj.create import Create
import pytest


@pytest.mark.parametrize('config',
                         [Config(['--job', 'toto',
                                  '--server', 'https://first',
                                  '--auth', 'tests/fixtures/auth.rc']),
                          Config(['--conf', 'tests/fixtures/conf-1-job.ini',
                                  '--jobs', 'toto_conf',
                                  '--server', 'first'])])
def test_create_trigger(config, mocker):
    builder = mocker.MagicMock()
    one_job = Create(config, builder)
    one_job.trigger()
    builder.assert_called_once_with(server='https://first',
                                    job='toto',
                                    auth={'username': 'foo',
                                          'password': 'bar'},
                                    params={})
