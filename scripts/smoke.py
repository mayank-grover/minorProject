"""Authenticated real API smoke test using a frozen public pilot image."""
import base64
import json
from pathlib import Path
from dotenv import dotenv_values
import httpx

settings = dotenv_values('.env')
sample = json.loads(Path('benchmark/manifests/pilot.jsonl').read_text().splitlines()[0])
payload = {'request_id': 'real-api-smoke-001', 'occurrence_id': sample['sample_id'],
    'article_url': sample['article_url'], 'revision_id': sample['revision_id'], 'image_url': sample['image_url'],
    'image_base64': base64.b64encode(Path(sample['local_image']).read_bytes()).decode(),
    'context': sample['context'], 'mode': 'context_aware', 'detail': 'concise'}
r = httpx.post('http://127.0.0.1:8000/describe', json=payload,
               headers={'Authorization': 'Bearer '+settings['LOCAL_BACKEND_TOKEN']}, timeout=130)
print('HTTP', r.status_code)
print(json.dumps(r.json(), indent=2))
r.raise_for_status()
Path('artifacts/api-smoke.json').write_text(json.dumps(r.json(), indent=2))
