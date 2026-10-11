"""Append-only paired runs, same prepared pixels/settings, no response cache."""
import argparse
import hashlib
import json
import platform
import time
import uuid
from pathlib import Path
from backend.models.smolvlm import SmolVLM
from backend.schemas import Context
from backend.data.images import prepare_image
from backend.engine.generate import run_generation
from backend.engine.prompts import build_prompt, PROMPT_VERSION


def run(manifest, output, model):
    path = Path(output); path.parent.mkdir(parents=True, exist_ok=True)
    existing = [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []
    config = model.configuration()
    fingerprint = hashlib.sha256(json.dumps(config, sort_keys=True).encode()).hexdigest()
    done = {(r['sample_id'], r['mode'], r['image_hash'], r['prompt_hash'], r['config_hash']) for r in existing}
    samples = [json.loads(line) for line in Path(manifest).read_text().splitlines() if line.strip()]
    if len({s['sample_id'] for s in samples}) != len(samples): raise ValueError('Duplicate sample IDs')
    with path.open('a') as stream:
        for sample in samples:
            context = Context(**sample['context'])
            image, _, digest, _ = prepare_image(Path(sample['local_image']).read_bytes())
            if digest != sample['image_hash']: raise ValueError(f"Prepared image changed: {sample['sample_id']}")
            for mode in ['image_only', 'context_aware']:
                prompt = build_prompt(context, mode)
                prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()
                key = (sample['sample_id'], mode, digest, prompt_hash, fingerprint)
                if key in done: continue
                record = {'run_id': str(uuid.uuid4()), 'sample_id': sample['sample_id'], 'mode': mode,
                    'status': 'failed', 'model_id': model.model_id, 'model_revision': model.revision,
                    'configuration': config, 'config_hash': fingerprint, 'image_hash': digest,
                    'prompt_version': PROMPT_VERSION, 'prompt_hash': prompt_hash, 'prompt': prompt,
                    'description': None, 'error': None, 'inference_ms': None,
                    'platform': platform.platform(), 'created_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}
                start = time.perf_counter()
                try:
                    record.update(run_generation(model, image, context, mode)); record['status'] = 'success'
                except Exception as exc:
                    for field in ['raw_output', 'inference_ms', 'tokens', 'finish_reason']:
                        if hasattr(exc, field): record[field] = getattr(exc, field)
                    record['error'] = {'code': getattr(exc, 'code', type(exc).__name__), 'message': str(exc)}
                record['total_ms'] = (time.perf_counter() - start) * 1000
                stream.write(json.dumps(record, ensure_ascii=False) + '\n'); stream.flush()
                print(sample['sample_id'], mode, record['status'], round(record['total_ms']), 'ms', flush=True)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--manifest', default='benchmark/manifests/pilot.jsonl'); parser.add_argument('--output', default='artifacts/runs/pilot.jsonl')
    args = parser.parse_args(); model = SmolVLM(); model.load(); run(args.manifest, args.output, model)
