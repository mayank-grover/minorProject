"""Local neural speech synthesis using Kokoro."""
import io
import logging
import threading
import wave

from backend.errors import ProjectError

log = logging.getLogger('wiki_describe.tts')
KOKORO_VOICES = (
    'af_heart', 'af_bella', 'af_sarah', 'af_nicole', 'af_sky',
    'am_adam', 'am_michael', 'bf_emma', 'bf_isabella', 'bm_george', 'bm_lewis',
)


class KokoroSpeech:
    """Lazy-loaded English Kokoro model; synthesis runs on CPU for portability."""

    def __init__(self):
        self._model = None
        self._pipelines = {}
        self._lock = threading.Lock()

    @property
    def ready(self):
        return self._model is not None

    def _load(self):
        if self._model is not None:
            return
        try:
            from kokoro import KModel, KPipeline
        except ImportError:
            raise ProjectError(
                'TTS_UNAVAILABLE',
                'Natural voice is not installed. Install requirements-tts.in and restart the backend.',
                503, True,
            ) from None

        # Keep one language-independent model in memory and light pipelines for US/UK G2P.
        try:
            self._model = KModel().eval().cpu()
            self._pipelines = {
                code: KPipeline(lang_code=code, model=False)
                for code in ('a', 'b')
            }
        except Exception:
            self._model = None
            self._pipelines = {}
            raise ProjectError(
                'TTS_MODEL_LOAD_FAILED',
                'Could not load natural voice assets. Check the first-run download or use the device voice.',
                503, True,
            ) from None

    def synthesize(self, text, voice, speed):
        import numpy as np

        with self._lock:
            self._load()
            pipeline = self._pipelines[voice[0]]
            chunks = []
            try:
                for result in pipeline(text, voice=voice, speed=speed, model=self._model):
                    if result.audio is not None:
                        chunks.append(result.audio.detach().cpu().numpy())
            except Exception:
                raise ProjectError(
                    'TTS_FAILED', 'Natural voice synthesis failed. Try the system voice or retry.', 503, True,
                ) from None

        if not chunks:
            raise ProjectError('TTS_EMPTY', 'Natural voice returned no audio. Try the system voice.', 502, True)

        audio = np.concatenate(chunks)
        pcm = np.clip(np.rint(audio * 32767), -32768, 32767).astype('<i2')
        output = io.BytesIO()
        with wave.open(output, 'wb') as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(24000)
            wav.writeframes(pcm.tobytes())
        return output.getvalue()

    def warmup(self):
        """Load model, cache every offered voice, and exercise inference once."""
        with self._lock:
            self._load()
            for index, voice in enumerate(KOKORO_VOICES, start=1):
                log.info('Preparing neural voice %d/%d: %s', index, len(KOKORO_VOICES), voice)
                self._pipelines[voice[0]].load_voice(voice)
        # Prime torch and the default inference path so the first user request skips cold start.
        self.synthesize('Natural narration is ready.', 'af_heart', 1.0)
