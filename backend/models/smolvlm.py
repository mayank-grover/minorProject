"""Real local inference. No network image fetching or context handling here."""
import os
import time
from dataclasses import dataclass

MODEL_ID = 'HuggingFaceTB/SmolVLM2-2.2B-Instruct'

@dataclass
class ModelOutput:
    text: str
    inference_ms: float
    tokens: int
    finish_reason: str

class SmolVLM:
    model_id = MODEL_ID

    def __init__(self, revision='main', device='auto', max_new_tokens=192):
        self.revision = revision
        self.device = device
        self.max_new_tokens = max_new_tokens
        self.ready = False

    def load(self):
        import torch
        from transformers import AutoProcessor, AutoModelForImageTextToText
        if self.device == 'auto':
            self.device = 'cuda' if torch.cuda.is_available() else 'mps' if torch.backends.mps.is_available() else 'cpu'
        self.dtype = torch.float32 if self.device == 'cpu' else torch.float16
        self.processor = AutoProcessor.from_pretrained(self.model_id, revision=self.revision)
        self.processor.image_processor.do_image_splitting = True
        self.processor.image_processor.size = {'longest_edge': 768}
        self.model = AutoModelForImageTextToText.from_pretrained(
            self.model_id, revision=self.revision, dtype=self.dtype,
            attn_implementation='eager', low_cpu_mem_usage=True,
        ).to(self.device).eval()
        self.revision = getattr(self.model.config, '_commit_hash', None) or self.revision
        from backend.engine.ocr import LocalOCR
        self.ocr = LocalOCR()
        self.ocr.load()
        self.ready = True

    def configuration(self):
        return {'model_id': self.model_id, 'revision': self.revision, 'device': self.device,
                'dtype': str(getattr(self, 'dtype', 'unloaded')), 'do_sample': False,
                'max_new_tokens': self.max_new_tokens, 'attention': 'eager',
                'processor': 'official; image splitting enabled; longest_edge=768; patch=384', 'preprocessing': 'rgb-768-v1',
                'ocr_engine': getattr(getattr(self, 'ocr', None), 'engine', 'unavailable'),
                'ocr_preprocessing': 'rgb-1600; tesseract-psm11+6; bounded-words-v1', 'image_routing': 'types-v1'}

    def generate(self, image, prompt, max_new_tokens=None):
        import torch
        if not self.ready:
            raise RuntimeError('Model is not loaded')
        messages = [{'role': 'user', 'content': [{'type': 'image'}, {'type': 'text', 'text': prompt}]}]
        text = self.processor.apply_chat_template(messages, add_generation_prompt=True, tokenize=False)
        inputs = self.processor(text=text, images=[image], return_tensors='pt')
        inputs = inputs.to(self.device, dtype=self.dtype)
        if 'pixel_values' not in inputs:
            raise RuntimeError('Processor did not produce vision inputs')
        self._sync(torch)
        start = time.perf_counter()
        with torch.inference_mode():
            budget = max_new_tokens or self.max_new_tokens
            output = self.model.generate(**inputs, do_sample=False, max_new_tokens=budget)
        self._sync(torch)
        elapsed = (time.perf_counter() - start) * 1000
        generated = output[0, inputs['input_ids'].shape[1]:]
        result = self.processor.decode(generated, skip_special_tokens=True).strip()
        return ModelOutput(result, elapsed, len(generated), 'length' if len(generated) >= budget else 'stop')

    def classify_image(self, image):
        prompt = ('Classify the visible image. Reply with exactly one word: '
                  'photo, flag, chart, map, process, or diagram. '
                  'A process shows ordered steps or a cycle. A chart plots data. '
                  'Use photo for ordinary photographs.')
        output = self.generate(image, prompt, max_new_tokens=8)
        kind = output.text.strip().lower().strip('." ')
        return kind if kind in ('photo', 'flag', 'chart', 'map', 'process', 'diagram') else 'photo'

    def _sync(self, torch):
        if self.device == 'mps':
            torch.mps.synchronize()
        elif self.device == 'cuda':
            torch.cuda.synchronize()
