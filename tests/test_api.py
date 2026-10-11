import time
from fastapi.testclient import TestClient
from backend.app import create_app
from backend.settings import Settings
from backend.errors import ProjectError

def client_for(model, **kwargs):
    return TestClient(create_app(Settings(token='test-token', extension_id='test-extension', load_model=False, **kwargs), model))

AUTH = {'Authorization': 'Bearer test-token'}

def test_real_contract_with_test_adapter(payload, fake_model):
    with client_for(fake_model) as client:
        assert client.get('/health').json()['model_ready'] is True
        response = client.post('/describe', json=payload, headers=AUTH)
        assert response.status_code == 200
        result = response.json()
        assert result['request_id'] == payload['request_id']
        assert result['model_id'] == 'unit-test-fixture'
        assert len(result['image_hash']) == 64
        payload['mode'] = 'image_only'
        assert client.post('/v1/descriptions', json=payload, headers=AUTH).status_code == 200
        assert 'SECRET_TITLE' not in fake_model.calls[-1][1]
        assert 'SECRET_CAPTION' not in fake_model.calls[-1][1]
        assert fake_model.calls[-1][0].size == (64,64)

def test_auth_origin_invalid_missing_and_image_errors(payload, fake_model):
    with client_for(fake_model) as client:
        assert client.post('/describe', json=payload).status_code == 401
        assert client.post('/describe', json=payload, headers={**AUTH, 'Origin': 'https://evil.example'}).status_code == 403
        assert client.post('/describe', json={**payload, 'mode': 'unknown'}, headers=AUTH).status_code == 422
        assert client.post('/describe', json={}, headers=AUTH).status_code == 422
        assert client.post('/describe', json={**payload, 'image_base64': 'bad'}, headers=AUTH).json()['error']['code'] == 'INVALID_IMAGE'
        assert client.post('/describe', content='x'*12_000_001, headers=AUTH).status_code == 413
        payload['image_url'] = 'http://127.0.0.1/private'
        assert client.post('/describe', json=payload, headers=AUTH).status_code == 422

def test_inference_error_no_secret_leak(payload, fake_model):
    def fail(*args): raise RuntimeError('SECRET_KEY')
    fake_model.generate = fail
    with client_for(fake_model) as client:
        response = client.post('/describe', json=payload, headers=AUTH)
        assert response.status_code == 503
        assert 'SECRET_KEY' not in response.text

def test_empty_and_unavailable(payload, fake_model):
    fake_model.ready = False
    with client_for(fake_model) as client:
        assert client.get('/health').json()['status'] == 'degraded'
        assert client.post('/describe', json=payload, headers=AUTH).status_code == 503
    fake_model.ready = True
    from backend.models.smolvlm import ModelOutput
    fake_model.generate = lambda *args: ModelOutput('', 1, 0, 'stop')
    with client_for(fake_model) as client:
        assert client.post('/describe', json=payload, headers=AUTH).json()['error']['code'] == 'EMPTY_OUTPUT'

def test_deadline_keeps_lane_busy(payload, fake_model):
    original = fake_model.generate
    def slow(*args): time.sleep(.15); return original(*args)
    fake_model.generate = slow
    with client_for(fake_model, timeout=.01) as client:
        assert client.post('/describe', json=payload, headers=AUTH).status_code == 504
        assert client.post('/describe', json=payload, headers=AUTH).status_code == 429
        time.sleep(.2)
        assert client.get('/health').json()['busy'] is False
