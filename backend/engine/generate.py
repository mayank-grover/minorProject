import hashlib
import json
import re
import time
from backend.errors import ProjectError
from backend.engine.prompts import build_prompt, PROMPT_VERSION
from backend.engine.image_types import inspect_image
from backend.engine.article_context import editorial_context, integrate_subject

def run_generation(model, image, context, mode, detail='concise', analysis=None, ocr_image=None, requested_type='auto'):
    analysis_start = time.perf_counter()
    try:
        analysis = analysis or inspect_image(model, image, context, mode, ocr_image, requested_type)
    except Exception:
        raise ProjectError('INFERENCE_FAILED', 'Image analysis failed. Check backend hardware and logs.', 503, True) from None
    analysis_ms = (time.perf_counter() - analysis_start) * 1000
    prompt = build_prompt(context, mode, detail, analysis)
    try:
        output = model.generate(image, prompt)
    except Exception:
        raise ProjectError('INFERENCE_FAILED', 'Local model inference failed. Check backend hardware and logs.', 503, True) from None
    raw = output.text.strip()
    def reject(code, message):
        error = ProjectError(code, message, 502, True)
        error.raw_output = raw
        error.inference_ms = output.inference_ms
        error.tokens = output.tokens
        error.finish_reason = output.finish_reason
        raise error
    if not raw:
        reject('EMPTY_OUTPUT', 'Model returned an empty description.')
    if re.search(r'<[^>]+>|```|\b\d+(?:\.\d+)?\s*%\s*(?:confiden|certain)', raw, re.I):
        reject('OUTPUT_REJECTED', 'Model returned unsupported formatting or confidence claims.')
    limit = 120 if detail == 'concise' else 250
    limitations = ['AI-generated; visual facts and contextual claims may be incorrect.']
    if analysis['image_type'] in ('chart', 'map', 'process', 'diagram'):
        if analysis['ocr']['status'] in ('unavailable', 'failed'):
            limitations.append('Local text recognition is unavailable; small labels may be missed.')
        else:
            limitations.append('Detected text can be misread; label positions do not prove connections or values.')
    if len(raw.split()) > limit:
        reject('OUTPUT_REJECTED', 'Description exceeded the word limit. Try again.')
    if output.finish_reason == 'length':
        limitations.append('Generation reached its token limit; the description may be incomplete.')
    data = context.model_dump() if hasattr(context, 'model_dump') else dict(context)
    editorial = editorial_context(context, mode, analysis['image_type'])
    description = integrate_subject(raw, editorial['subject'])
    if editorial['subject']:
        limitations.append('Names are associated using article source text, not facial recognition.')
    actual_context = editorial['source']
    if mode == 'context_aware' and (data.get('caption') or '').lower().startswith('conservation status:'):
        actual_context = {'caption': data['caption']}
    return {'description': description, 'raw_output': raw, 'prompt': prompt,
            'prompt_version': PROMPT_VERSION, 'prompt_hash': hashlib.sha256(prompt.encode()).hexdigest(),
            'context_hash': hashlib.sha256(json.dumps(actual_context, sort_keys=True).encode()).hexdigest(),
            'inference_ms': output.inference_ms, 'analysis_ms': analysis_ms, 'image_type':analysis['image_type'],
            'description_focus':editorial['focus'], 'resolved_subject':editorial['subject'],
            'type_source':analysis['type_source'], 'ocr_status':analysis['ocr']['status'], 'ocr_engine':analysis['ocr']['engine'],
            'ocr_ms':analysis['ocr']['ms'], 'ocr_lines':analysis['ocr']['lines'], 'tokens': output.tokens,
            'finish_reason': output.finish_reason, 'limitations': limitations}
