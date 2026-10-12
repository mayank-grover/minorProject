import errno
import io
import json
from types import SimpleNamespace
import run


class PortProbe:
    def __init__(self, busy): self.busy = busy
    def __enter__(self): return self
    def __exit__(self, *args): pass
    def bind(self, address):
        if self.busy: raise OSError(errno.EADDRINUSE, 'already in use')


def occupied(monkeypatch, health):
    monkeypatch.setattr(run.socket, 'socket', lambda *args: PortProbe(True))
    opener = SimpleNamespace(open=lambda *args, **kwargs: io.StringIO(json.dumps(health)))
    monkeypatch.setattr(run, 'build_opener', lambda *args: opener)


def test_ready_backend_does_not_launch_a_second_model(monkeypatch, capsys):
    occupied(monkeypatch, {'processing':'local', 'schema_version':'1.0',
                          'model_id':'HuggingFaceTB/SmolVLM2-2.2B-Instruct',
                          'model_ready':True, 'status':'ok'})
    def forbidden(*args): raise AssertionError('Must not launch a second server')
    monkeypatch.setattr(run.os, 'execve', forbidden)
    assert run.main() == 0
    assert 'already running and ready' in capsys.readouterr().out


def test_unrelated_service_is_not_treated_as_ready(monkeypatch, capsys):
    occupied(monkeypatch, {'status':'ok', 'model_ready':True})
    assert run.check_existing_server() == 1
    assert 'another or unresponsive service' in capsys.readouterr().err


def test_degraded_backend_reports_model_problem(monkeypatch, capsys):
    occupied(monkeypatch, {'processing':'local', 'schema_version':'1.0',
                          'model_id':'HuggingFaceTB/SmolVLM2-2.2B-Instruct',
                          'model_ready':False, 'status':'degraded'})
    assert run.check_existing_server() == 1
    assert 'model is not ready' in capsys.readouterr().err


def test_free_port_allows_normal_startup(monkeypatch):
    monkeypatch.setattr(run.socket, 'socket', lambda *args: PortProbe(False))
    assert run.check_existing_server() is None
