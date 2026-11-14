"""Freeze collect_live.cjs payloads into a manifest with local image bytes, hashes and licenses.

Two renditions per occurrence:
  extension: what the extension sends today on a 2x (Retina) display, i.e. the largest srcset
             candidate (falls back to src). Chrome picks currentSrc by device pixel ratio.
  large:     the 960 px Wikimedia thumbnail bucket (or the original if smaller).
Raw bytes are stored, because the API prepares 768 px (model) and 1600 px (OCR) images from them.
"""
import argparse
import hashlib
import json
import re
import time
from pathlib import Path
from urllib.parse import unquote
import httpx
from bs4 import BeautifulSoup
from backend.data.images import fetch_image, prepare_image
from backend.settings import Settings

UA = Settings().user_agent
API = 'https://en.wikipedia.org/w/api.php'


def file_title(url):
    path = unquote(url.split('?')[0])
    match = re.search(r'/thumb/[0-9a-f]/[0-9a-f]{2}/([^/]+)/', path) or re.search(r'/[0-9a-f]/[0-9a-f]{2}/([^/]+)$', path)
    return 'File:' + match.group(1) if match else None


def file_info(title):
    for attempt in range(4):
        r = httpx.get(API, headers={'User-Agent': UA}, timeout=20, params={
            'action': 'query', 'titles': title, 'prop': 'imageinfo', 'format': 'json',
            'iiprop': 'url|sha1|size|extmetadata|mime', 'iiurlwidth': 960})
        if r.status_code == 200:
            page = next(iter(r.json()['query']['pages'].values()))
            return (page.get('imageinfo') or [None])[0]
        print('  imageinfo HTTP', r.status_code, 'retrying', flush=True); time.sleep(5 * (attempt + 1))
    return None


def text(html):
    return BeautifulSoup(html or '', 'html.parser').get_text(' ', strip=True)


def freeze(raw, splits, output, image_dir):
    split_of = {}
    for line in Path(splits).read_text().splitlines():
        if line.strip() and not line.startswith('#'):
            spec, split = line.split()
            split_of[spec.split('=')[0]] = split
    root = Path(image_dir); root.mkdir(parents=True, exist_ok=True)
    counters, records = {}, []
    for line in Path(raw).read_text().splitlines():
        if not line.strip(): continue
        row = json.loads(line); split = split_of[row['slug']]
        counters[split] = counters.get(split, 0) + 1
        sample_id = f'live-{split}-{counters[split]:02d}'
        scales = sorted(row['renditions'], key=float)
        urls = {'extension': row['renditions'][scales[-1]]}
        title = file_title(urls['extension']); info = file_info(title) if title else None
        if info: urls['large'] = info.get('thumburl') or info['url']
        record = {'sample_id': sample_id, 'split': split, 'slug': row['slug'], 'category': row['category'],
                  'occurrence_index': row['index'], 'eligible_count': row['eligible_count'],
                  'display_width': row['display_width'], 'extension_scale': scales[-1],
                  'article_url': row['payload']['article_url'], 'revision_id': row['payload']['revision_id'],
                  'context': row['payload']['context'], 'file_title': title, 'retrieved_utc': row['retrieved_utc'],
                  'license': text(info and info.get('extmetadata', {}).get('LicenseShortName', {}).get('value')),
                  'author': text(info and info.get('extmetadata', {}).get('Artist', {}).get('value'))[:300],
                  'file_sha1': info and info.get('sha1'), 'original_size': info and [info.get('width'), info.get('height')],
                  'renditions': {}, 'association_review': 'pending'}
        for name, url in urls.items():
            try:
                data = fetch_image(url, UA)
                image, _, prepared_hash, _ = prepare_image(data)
                ext = re.search(r'\.(\w+)$', url.split('?')[0]).group(1).lower()
                path = root / f'{sample_id}-{name}.{ext}'; path.write_bytes(data)
                record['renditions'][name] = {'url': url, 'path': str(path), 'bytes_sha256': hashlib.sha256(data).hexdigest(),
                                              'prepared_hash': prepared_hash, 'size': list(image.size)}
            except Exception as exc:
                record['renditions'][name] = {'url': url, 'error': str(exc)}
            time.sleep(0.3)
        records.append(record)
        sizes = {k: v.get('size') or v.get('error') for k, v in record['renditions'].items()}
        print(sample_id, row['slug'], f"#{row['index']}", record['license'] or 'NO LICENSE', sizes, flush=True)
    Path(output).write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in records))
    print('Saved', len(records), 'occurrences to', output)


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--raw', default='artifacts/live/raw.jsonl'); p.add_argument('--splits', default='benchmark/manifests/live_articles.txt')
    p.add_argument('--output', default='benchmark/manifests/live.jsonl'); p.add_argument('--image-dir', default='artifacts/live/img')
    a = p.parse_args(); freeze(a.raw, a.splits, a.output, a.image_dir)
