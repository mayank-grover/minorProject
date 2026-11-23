"""Groq vision adapter implementing the backend's local model interface."""
import base64
import io
import re
import time

import httpx

from backend.engine.ocr import LocalOCR
from backend.errors import ProjectError
from backend.models.smolvlm import ModelOutput


class GroqVision:
    """Send prepared pixels and prompts to Groq's vision chat-completions API."""

    endpoint = 'https://api.groq.com/openai/v1/chat/completions'
    revision = 'cloud-api'
    device = 'cloud'

    def __init__(self, api_key, model_id='qwen/qwen3.8-27b', timeout=120):
        self.api_key = api_key.strip()
        self.model_id = model_id
        self.timeout = timeout
        self.ready = False
        self.ocr = LocalOCR()

    def load(self):
        if not self.api_key:
            raise RuntimeError('GROQ_API_KEY is not configured')
        self.ocr.load()
        self.ready = True

    def configuration(self):
        return {
            'provider': 'groq',
            'model_id': self.model_id,
            'revision': self.revision,
            'device': self.device,
            'ocr_engine': self.ocr.engine,
            'preprocessing': 'rgb-768-v1',
            'api': 'groq-chat-completions-vision-v1',
        }

    @staticmethod
    def _image_data_url(image):
        output = io.BytesIO()
        image.save(output, format='PNG', optimize=True)
        encoded = base64.b64encode(output.getvalue()).decode('ascii')
        return 'data:image/png;base64,' + encoded

    def _complete(self, image, prompt, max_completion_tokens=384):
        if not self.ready:
            raise RuntimeError('Groq provider is not initialized')
        payload = {
            'model': self.model_id,
            'messages': [{
                'role': 'user',
                'content': [
                    {'type': 'text', 'text': prompt},
                    {'type': 'image_url', 'image_url': {'url': self._image_data_url(image)}},
                ],
            }],
            'max_completion_tokens': max_completion_tokens,
            'temperature': 0.1,
            'stream': False,
        }
        start = time.perf_counter()
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(
                    self.endpoint,
                    headers={'Authorization': f'Bearer {self.api_key}'},
                    json=payload,
                )
        except httpx.TimeoutException:
            raise ProjectError('GROQ_TIMEOUT', 'Groq image analysis timed out. Try again.', 504, True) from None
        except httpx.HTTPError:
            raise ProjectError('GROQ_CONNECTION_FAILED', 'Could not connect to Groq. Check the network and try again.', 502, True) from None

        if response.status_code == 429:
            raise ProjectError('GROQ_RATE_LIMITED', 'Groq rate limit reached. Wait briefly and retry.', 429, True)
        if response.status_code in (401, 403):
            raise ProjectError('GROQ_AUTH_FAILED', 'Groq rejected the API key. Check GROQ_API_KEY in .env.', 503)
        if response.status_code >= 400:
            # Do not return upstream response bodies; they may include request details.
            raise ProjectError('GROQ_REQUEST_FAILED', f'Groq rejected the request (HTTP {response.status_code}). Check the configured model and image limits.', 502, response.status_code >= 500)
        try:
            body = response.json()
            choice = body['choices'][0]
            text = choice['message']['content']
            if not isinstance(text, str):
                raise TypeError('non-text completion')
        except (ValueError, KeyError, IndexError, TypeError):
            raise ProjectError('GROQ_INVALID_RESPONSE', 'Groq returned an unexpected response. Try again.', 502, True) from None
        usage = body.get('usage') or {}
        return text, (time.perf_counter() - start) * 1000, int(usage.get('completion_tokens') or 0), choice.get('finish_reason') or 'stop'

    def classify_image(self, image):
        """Classify once so the shared prompt builder can select image-specific guidance."""
        prompt = (
            'Classify the image using exactly one lowercase label: photo, flag, chart, map, process, or diagram. '
            'Use process for a lifecycle or flowchart. Use diagram for a labeled schematic or table. '
            'Return only the label.'
        )
        text, _, _, _ = self._complete(image, prompt, max_completion_tokens=24)
        match = re.search(r'\b(photo|flag|chart|map|process|diagram)\b', text.lower())
        return match.group(1) if match else 'photo'

    def generate(self, image, prompt, max_new_tokens=None):
        text, elapsed, tokens, finish_reason = self._complete(
            image, prompt, max_completion_tokens=max_new_tokens or 384,
        )
        return ModelOutput(text.strip(), elapsed, tokens, 'length' if finish_reason == 'length' else 'stop')
