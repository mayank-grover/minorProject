import hashlib
import json
import re
import time
from backend.errors import ProjectError
from backend.engine.prompts import build_prompt, PROMPT_VERSION
from backend.engine.image_types import inspect_image
from backend.engine.article_context import editorial_context, integrate_subject

COPY_RUN = 12  # pilot: verbatim copies shared 44-97 words with context; normal outputs <= 8


def copied_run(text, context):
    """True if text repeats COPY_RUN consecutive words of the supplied article text."""
    data = context.model_dump() if hasattr(context, 'model_dump') else dict(context)
    source = ' '.join(filter(None, [data.get('nearby_text'), data.get('page_summary'), data.get('caption'), *data.get('image_overview', [])]))
    words = lambda t: re.findall(r'\w+', t.lower())
    grams = lambda w: {tuple(w[i:i+COPY_RUN]) for i in range(len(w) - COPY_RUN + 1)}
    return bool(grams(words(text)) & grams(words(source)))


def run_generation(model, image, context, mode, detail='concise', analysis=None, ocr_image=None, requested_type='auto'):
    analysis_start = time.perf_counter()
    try:
        analysis = analysis or inspect_image(model, image, context, mode, ocr_image, requested_type)
    except Exception:
        raise ProjectError('INFERENCE_FAILED', 'Image analysis failed. Check backend hardware and logs.', 503, True) from None
    analysis_ms = (time.perf_counter() - analysis_start) * 1000
    prompt = build_prompt(context, mode, detail, analysis)
    def generate(text):
        try:
            return model.generate(image, text)
        except Exception:
            raise ProjectError('INFERENCE_FAILED', 'Local model inference failed. Check backend hardware and logs.', 503, True) from None
    output = generate(prompt)
    raw = output.text.strip()
    repair = None
    if mode == 'context_aware' and copied_run(raw, context):
        # One recorded retry without long article prose; title and caption stay.
        reduced = context.model_copy(update={'nearby_text': None, 'page_summary': None, 'image_overview': []})
        retry_prompt = build_prompt(reduced, mode, detail, analysis)
        first, output = output, generate(retry_prompt)
        output.inference_ms += first.inference_ms
        repair = {'reason': 'context_copy', 'first_output': raw,
                  'retry_prompt_hash': hashlib.sha256(retry_prompt.encode()).hexdigest()}
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
    shortened_from = None
    if len(raw.split()) > limit:
        # Greedy decoding repeats the same output, so rejecting made Retry useless.
        # Keep whole leading sentences within the limit; reject only if none fit.
        kept = []
        for sentence in re.split(r'(?<=[.!?])\s+', raw):
            if len(' '.join(kept + [sentence]).split()) > limit: break
            kept.append(sentence)
        if not kept:
            reject('OUTPUT_REJECTED', 'Description exceeded the word limit. Try again.')
        shortened_from, raw = len(raw.split()), ' '.join(kept)
        limitations.append('Shortened to the length limit; later details were left out.')
    if repair and copied_run(raw, context):
        limitations.append('Parts of this description repeat the article text.')
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
            'finish_reason': output.finish_reason, 'limitations': limitations, 'repair': repair, 'shortened_from_words': shortened_from}
