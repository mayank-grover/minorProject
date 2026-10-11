import hashlib
import json
import re
import time
from backend.errors import ProjectError
from backend.engine.prompts import build_prompt, PROMPT_VERSION

def run_generation(model, image, context, mode, detail='concise'):
    prompt = build_prompt(context, mode, detail)
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
    if len(raw.split()) > limit:
        reject('OUTPUT_REJECTED', 'Description exceeded the word limit. Try again.')
    if output.finish_reason == 'length':
        limitations.append('Generation reached its token limit; the description may be incomplete.')
    data = context.model_dump() if hasattr(context, 'model_dump') else dict(context)
    actual_context = {} if mode == 'image_only' else {k: v for k, v in data.items() if k != 'existing_alt'}
    if mode == 'context_aware' and (data.get('caption') or '').lower().startswith('conservation status:'):
        actual_context = {'caption': data['caption']}
    return {'description': raw, 'raw_output': raw, 'prompt': prompt,
            'prompt_version': PROMPT_VERSION, 'prompt_hash': hashlib.sha256(prompt.encode()).hexdigest(),
            'context_hash': hashlib.sha256(json.dumps(actual_context, sort_keys=True).encode()).hexdigest(),
            'inference_ms': output.inference_ms, 'tokens': output.tokens,
            'finish_reason': output.finish_reason, 'limitations': limitations}
