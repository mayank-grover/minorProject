"""Collect one freely licensed Wikimedia occurrence from each candidate article.
Store frozen article HTML, file metadata, context and prepared raster hashes.
Network failures and exclusions are retained separately; no synthetic context.
"""
import argparse
import json
import os
import time
from pathlib import Path
from urllib.parse import unquote, quote, urljoin
import httpx
from bs4 import BeautifulSoup
from backend.data.images import fetch_image, prepare_image
from backend.schemas import Context

ARTICLES = [
    ('Common_sunflower', 'photograph'), ('Golden_Gate_Bridge', 'photograph'),
    ('Albert_Einstein', 'portrait'), ('Moon', 'astronomy'),
    ('Bicycle', 'artifact'), ('Monarch_butterfly', 'photograph'),
    ('Water_cycle', 'diagram'), ('Periodic_table', 'diagram'),
    ('World_map', 'map'), ('Solar_System', 'diagram'),
    ('Volcano', 'photograph'), ('Bar_chart', 'chart')
]
API = 'https://en.wikipedia.org/w/api.php'
UA = os.environ.get('WIKIMEDIA_USER_AGENT', 'WikiImageAccessibility/0.1 (academic local pilot; configure contact for team use)')

def plain(node, limit):
    return node.get_text(' ', strip=True)[:limit] if node else None

def collect(output, limit=10):
    root = Path('artifacts/dataset'); root.mkdir(parents=True, exist_ok=True)
    records, failures = [], []
    with httpx.Client(timeout=30, headers={'User-Agent': UA}, follow_redirects=False) as client:
        for slug, category in ARTICLES:
            if len(records) >= limit: break
            try:
                r = client.get(API, params={'action': 'parse', 'page': slug.replace('_', ' '), 'prop': 'text|revid', 'format': 'json', 'redirects': 1})
                r.raise_for_status(); parsed = r.json()['parse']
                html = parsed['text']['*']; soup = BeautifulSoup(html, 'html.parser')
                candidates = soup.select('figure img,.thumb img,.infobox img,.gallerybox img')
                chosen = None
                for img in candidates:
                    if img.find_parent(class_=['navbox', 'metadata', 'ambox']): continue
                    anchor = img.find_parent('a', href=True)
                    href = anchor['href'] if anchor else ''
                    # MediaWiki HTML uses /wiki/File: or ./File: for content file links.
                    if 'File:' not in href: continue
                    file_title = 'File:' + unquote(href.split('File:', 1)[1].split('#')[0])
                    meta_response = client.get(API, params={'action': 'query', 'titles': file_title, 'prop': 'imageinfo', 'iiprop': 'url|sha1|timestamp|extmetadata|size', 'iiurlwidth': 768, 'format': 'json'})
                    meta_response.raise_for_status()
                    page = next(iter(meta_response.json()['query']['pages'].values()))
                    if not page.get('imageinfo'): continue
                    meta = page['imageinfo'][0]; ext = meta.get('extmetadata', {})
                    license_text = ext.get('LicenseShortName', {}).get('value', '')
                    if not any(x in license_text.lower() for x in ['cc', 'public domain', 'pd', 'gfdl']):
                        failures.append({'article': slug, 'file': file_title, 'reason': 'License not recognized as freely redistributable', 'license': license_text}); continue
                    url = meta.get('thumburl')
                    if not url: continue
                    chosen = (img, file_title, meta, url, license_text, ext); break
                if not chosen: raise ValueError('No supported freely licensed occurrence found')
                img, file_title, meta, url, license_text, ext = chosen
                container = img.find_parent('figure') or img.find_parent(class_='thumb') or img.find_parent(class_='gallerybox') or img.find_parent('td')
                caption = container.select_one('figcaption,.thumbcaption,.gallerytext,.infobox-caption') if container else None
                heading = img.find_previous(['h2', 'h3', 'h4'])
                preceding = img.find_previous('p'); following = img.find_next('p')
                nearby = ' '.join(filter(None, [plain(preceding, 1600), plain(following, 1600)]))
                nearby = ' '.join(nearby.split()[:240]) or None
                context = Context(article_title=parsed['title'], caption=plain(caption, 1200), section_heading=plain(heading, 300), nearby_text=nearby,
                                  existing_alt=img.get('alt') if img.has_attr('alt') else None)
                data = fetch_image(url, UA)
                image, prepared, digest, animated = prepare_image(data)
                sample_id = f'pilot-{len(records)+1:02d}'
                image_path = root / f'{sample_id}.png'; image_path.write_bytes(prepared)
                (root / f'{sample_id}.html').write_text(html)
                records.append({'sample_id': sample_id, 'article_url': 'https://en.wikipedia.org/wiki/' + quote(parsed['title'].replace(' ', '_')),
                    'revision_id': parsed['revid'], 'permanent_link': f"https://en.wikipedia.org/w/index.php?oldid={parsed['revid']}",
                    'image_url': url, 'local_image': str(image_path), 'image_hash': digest, 'file_title': file_title,
                    'file_sha1': meta['sha1'], 'file_timestamp': meta['timestamp'], 'file_page': meta['descriptionurl'],
                    'license': license_text, 'license_url': ext.get('LicenseUrl', {}).get('value'),
                    'author': BeautifulSoup(ext.get('Artist', {}).get('value', ''), 'html.parser').get_text(' ', strip=True),
                    'attribution': BeautifulSoup(ext.get('Attribution', {}).get('value', ''), 'html.parser').get_text(' ', strip=True),
                    'retrieved_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), 'image_category': category,
                    'split': 'development_pilot', 'context': context.model_dump(), 'animated_first_frame': animated,
                    'association_review': 'pending; automatically extracted, inspect frozen HTML and image'})
                print(sample_id, parsed['title'], license_text, flush=True)
            except Exception as exc:
                failures.append({'article': slug, 'reason': str(exc)})
                print('Excluded:', slug, str(exc), flush=True)
            time.sleep(1)
    Path(output).parent.mkdir(parents=True, exist_ok=True)
    Path(output).write_text(''.join(json.dumps(record, ensure_ascii=False) + '\n' for record in records))
    Path(output).with_suffix('.exclusions.json').write_text(json.dumps(failures, indent=2))
    print(f'Saved {len(records)} real examples to {output}', flush=True)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--output', default='benchmark/manifests/pilot.jsonl'); parser.add_argument('--limit', type=int, default=10)
    args = parser.parse_args(); collect(args.output, args.limit)
