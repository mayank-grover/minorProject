"""Re-download a frozen manifest's images and verify each prepared hash.

Uses the stored image_url and the same preprocessing as runs; never rebuilds context.
If the Commons file was re-uploaded since, the archived version matching the stored
file_sha1 is used instead. A remaining mismatch is reported and nothing is written.
"""
import argparse
import json
import sys
import time
from pathlib import Path
import httpx
from backend.data.images import fetch_image, prepare_image
from backend.settings import Settings

UA = Settings().user_agent


def archived_url(s):
    """Thumbnail URL of the file version whose sha1 the manifest recorded, or None."""
    r = httpx.get('https://commons.wikimedia.org/w/api.php', headers={'User-Agent': UA}, timeout=20, params={
        'action': 'query', 'titles': s['file_title'], 'prop': 'imageinfo', 'iiprop': 'sha1|url',
        'iilimit': 50, 'iiurlwidth': s['image_url'].split('/')[-1].split('px-')[0], 'format': 'json'})
    info = next(iter(r.json()['query']['pages'].values())).get('imageinfo', [])
    return next((i['thumburl'] for i in info if i['sha1'] == s['file_sha1']), None)


def prepared(url):
    _, data, digest, _ = prepare_image(fetch_image(url, UA))
    return data, digest


def fetch(manifest):
    bad = 0
    for line in Path(manifest).read_text().splitlines():
        if not line.strip(): continue
        s = json.loads(line); path = Path(s['local_image'])
        try:
            data, digest = prepared(s['image_url'])
            if digest != s['image_hash'] and (url := archived_url(s)):
                data, digest = prepared(url)
        except Exception as exc:
            print(s['sample_id'], 'FETCH_FAILED', exc); bad += 1; continue
        if digest != s['image_hash']:
            print(s['sample_id'], 'HASH_MISMATCH', digest); bad += 1; continue
        path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(data)
        print(s['sample_id'], 'ok', path); time.sleep(1)
    return bad


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('--manifest', default='benchmark/manifests/pilot.jsonl')
    sys.exit(1 if fetch(p.parse_args().manifest) else 0)
