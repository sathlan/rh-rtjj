from rtjj.create import Config
from rtjj.create import Create
import pytest


@pytest.mark.parametrize('config',
                         [Config(['--job', 'foo',
                                  '--job', 'bar',
                                  '--server', 'https://first.com',
                                  '--param', 'PATCH_FILE0=https://file_server/patch0',
                                  '--param', 'PATCH_FILE1=https://file_server/patch1',
                                  '--param', 'TIMEOUT=3600',
                                  '--auth', 'tests/fixtures/auth.rc']),
                          Config(['--conf', 'tests/fixtures/conf-1-job.ini',
                                  '--jobs', 'FOO-CONF'])])
def test_create_trigger(config, mocker):
    builder = mocker.MagicMock()
    one_job = Create(config, builder)
    one_job.trigger()
    builder.assert_any_call(server='https://first.com',
                            job='bar',
                            auth={'username': 'foo',
                                  'password': 'bar'},
                            params={
                                'PATCH_FILE0': 'https://file_server/patch0',
                                'PATCH_FILE1': 'https://file_server/patch1',
                                'TIMEOUT': '3600'
                            })
    builder.assert_any_call(server='https://first.com',
                            job='foo',
                            auth={'username': 'foo',
                                  'password': 'bar'},
                            params={
                                'PATCH_FILE0': 'https://file_server/patch0',
                                'PATCH_FILE1': 'https://file_server/patch1',
                                'TIMEOUT': '3600'
                            })
