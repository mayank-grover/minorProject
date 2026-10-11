import base64
import io
import pytest
from PIL import Image
from backend.models.smolvlm import ModelOutput

class FakeModel:
    model_id = 'unit-test-fixture'
    revision = 'test-1'
    ready = True
    calls = []
    def configuration(self): return {'fixture': True}
    def generate(self, image, prompt):
        self.calls.append((image.copy(), prompt))
        return ModelOutput('A red rectangle is centered on a white background.', 1.0, 12, 'stop')

@pytest.fixture
def fake_model():
    model = FakeModel(); model.calls = []; return model

@pytest.fixture
def payload():
    buffer = io.BytesIO(); Image.new('RGB', (64,64), 'red').save(buffer, format='PNG')
    return {'request_id': 'test-001', 'occurrence_id': 'image-1',
            'article_url': 'https://en.wikipedia.org/wiki/Rectangle',
            'image_url': 'https://upload.wikimedia.org/wikipedia/commons/a/ab/Test.png',
            'image_base64': base64.b64encode(buffer.getvalue()).decode(),
            'context': {'article_title': 'SECRET_TITLE', 'caption': 'SECRET_CAPTION'}}
