"""Boson AI Higgs TTS 3 adapter for multilingual cloud narration."""
import httpx

from backend.errors import ProjectError


class BosonSpeech:
    endpoint = 'https://api.boson.ai/v1/audio/speech'
    model_id = 'higgs-tts-3'
    max_audio_bytes = 16 * 1024 * 1024

    def __init__(self, api_key, model_id='higgs-tts-3', timeout=120):
        self.api_key = api_key.strip()
        self.model_id = model_id
        self.timeout = timeout

    @property
    def ready(self):
        return bool(self.api_key)

    def synthesize(self, text, voice='default', speed=1.0, language='en'):
        if not self.api_key:
            raise ProjectError('BOSON_TTS_UNAVAILABLE', 'Configure BOSON_API_KEY in the backend .env file to use Boson voice.', 503)

        delivery = ''
        if speed <= 0.85:
            delivery = '<|prosody:speed_slow|>'
        elif speed >= 1.15:
            delivery = '<|prosody:speed_fast|>'
        language_code = 'hin' if language == 'hi' else 'eng'
        payload = {
            'model': self.model_id,
            'input': delivery + text,
            'voice': voice,
            'response_format': 'mp3',
            'stream': False,
            'normalize': True,
            'language': language_code,
        }
        try:
            with httpx.Client(timeout=self.timeout) as client:
                with client.stream('POST', self.endpoint,
                                   headers={'Authorization': f'Bearer {self.api_key}'},
                                   json=payload) as response:
                    if response.status_code == 401 or response.status_code == 403:
                        raise ProjectError('BOSON_TTS_AUTH_FAILED', 'Boson rejected the API key. Check BOSON_API_KEY.', 503)
                    if response.status_code == 429:
                        raise ProjectError('BOSON_TTS_RATE_LIMITED', 'Boson rate limit reached. Wait briefly and retry.', 429, True)
                    if response.status_code >= 400:
                        raise ProjectError('BOSON_TTS_REQUEST_FAILED', f'Boson rejected the speech request (HTTP {response.status_code}). Check the account, voice, and API limits.', 502, response.status_code >= 500)
                    content_type = response.headers.get('content-type', '').split(';', 1)[0].strip().lower()
                    if content_type not in ('audio/mpeg', 'audio/mp3'):
                        raise ProjectError('BOSON_TTS_INVALID_RESPONSE', 'Boson returned an unexpected audio format.', 502, True)
                    declared_size = int(response.headers.get('content-length') or 0)
                    if declared_size > self.max_audio_bytes:
                        raise ProjectError('BOSON_TTS_AUDIO_TOO_LARGE', 'Generated audio exceeds the playback size limit.', 502)
                    chunks = []
                    size = 0
                    for chunk in response.iter_bytes():
                        size += len(chunk)
                        if size > self.max_audio_bytes:
                            raise ProjectError('BOSON_TTS_AUDIO_TOO_LARGE', 'Generated audio exceeds the playback size limit.', 502)
                        chunks.append(chunk)
                    audio = b''.join(chunks)
        except ProjectError:
            raise
        except httpx.TimeoutException:
            raise ProjectError('BOSON_TTS_TIMEOUT', 'Boson speech generation timed out. Try again.', 504, True) from None
        except httpx.HTTPError:
            raise ProjectError('BOSON_TTS_CONNECTION_FAILED', 'Could not connect to Boson. Check the network and try again.', 502, True) from None
        if not audio:
            raise ProjectError('BOSON_TTS_EMPTY', 'Boson returned empty audio. Try again.', 502, True)
        return audio, 'audio/mpeg'
