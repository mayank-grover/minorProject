"""Run a frozen live manifest through the real API code path (in-process FastAPI + loaded model).

Same request shape the extension sends (bytes in image_base64, extracted context), so results
reflect the product. Append-only and resumable per (sample, rendition, mode).
Usage: python -m benchmark.run_api --split dev --rendition extension --output artifacts/runs/live-dev-ext.jsonl
"""
import argparse
import base64
import json
import platform
import time
from importlib.metadata import version
from pathlib import Path
from fastapi.testclient import TestClient
from backend.app import create_app
from backend.models.smolvlm import SmolVLM
from backend.settings import Settings

RUNTIME = {'python': platform.python_version(), **{p: version(p) for p in ['torch', 'transformers', 'pillow']}}


def run(manifest, split, renditions, modes, output, client, configuration):
    path = Path(output); path.parent.mkdir(parents=True, exist_ok=True)
    done = {(r['sample_id'], r['rendition'], r['mode']) for r in map(json.loads, path.read_text().splitlines())} if path.exists() else set()
    samples = [json.loads(l) for l in Path(manifest).read_text().splitlines() if l.strip()]
    with path.open('a') as stream:
        for s in samples:
            if split != 'all' and s['split'] != split: continue
            for rendition in renditions:
                image = s['renditions'][rendition]
                for mode in modes:
                    if (s['sample_id'], rendition, mode) in done: continue
                    body = {'request_id': f"{s['sample_id']}-{rendition}-{mode}"[:64], 'occurrence_id': s['sample_id'],
                            'article_url': s['article_url'], 'revision_id': s['revision_id'], 'image_url': image['url'],
                            'image_base64': base64.b64encode(Path(image['path']).read_bytes()).decode(),
                            'context': s['context'], 'mode': mode, 'detail': 'concise'}
                    start = time.perf_counter()
                    response = client.post('/v1/descriptions', json=body, headers={'Authorization': 'Bearer ' + Settings().token})
                    data = response.json()
                    record = {'sample_id': s['sample_id'], 'split': s['split'], 'category': s['category'], 'rendition': rendition,
                              'mode': mode, 'http_status': response.status_code, 'status': 'success' if response.status_code == 200 else 'failed',
                              'wall_ms': (time.perf_counter() - start) * 1000, 'image_bytes_sha256': image['bytes_sha256'],
                              'configuration': configuration, 'runtime': RUNTIME, 'platform': platform.platform(),
                              'created_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                              **({'response': data} if response.status_code == 200 else {'error': data.get('error')})}
                    stream.write(json.dumps(record, ensure_ascii=False) + '\n'); stream.flush()
                    print(s['sample_id'], rendition, mode, record['status'], round(record['wall_ms']), 'ms',
                          (data.get('description') or str(data.get('error')))[:90], flush=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--manifest', default='benchmark/manifests/live.jsonl'); p.add_argument('--split', default='dev', choices=['dev', 'test', 'all'])
    p.add_argument('--rendition', nargs='+', default=['extension']); p.add_argument('--mode', nargs='+', default=['image_only', 'context_aware'])
    p.add_argument('--output', required=True)
    a = p.parse_args(); settings = Settings()
    model = SmolVLM(settings.revision, settings.device, settings.max_tokens, settings.model_id); model.load()
    with TestClient(create_app(settings, model=model)) as client:
        run(a.manifest, a.split, a.rendition, a.mode, a.output, client, model.configuration())
