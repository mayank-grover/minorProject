import argparse
import csv
import html
import json
import statistics
from pathlib import Path

METRICS = ['visual_factuality', 'contextual_relevance', 'usefulness', 'clarity_concision', 'unsupported_claims']

def analyze(manifest, runs, output_dir):
    samples = {x['sample_id']: x for x in (json.loads(line) for line in Path(manifest).read_text().splitlines() if line.strip())}
    records = [json.loads(line) for line in Path(runs).read_text().splitlines() if line.strip()]
    if len({(r.get('config_hash'), r.get('prompt_version')) for r in records}) > 1:
        raise ValueError('Mixed experiment configurations: analyze separate run files.')
    pairs = {}
    for r in records: pairs.setdefault(r['sample_id'], {})[r['mode']] = r
    directory = Path(output_dir); directory.mkdir(parents=True, exist_ok=True)
    fields = ['sample_id', 'article_url', 'image_url', 'caption', 'image_only_output', 'context_aware_output',
              'image_only_latency_ms', 'context_aware_latency_ms', 'image_only_error', 'context_aware_error', 'reviewer_id']
    fields += [f'{mode}_{metric}' for mode in ['image_only', 'context_aware'] for metric in METRICS] + ['review_notes']
    rows = []
    for sample_id, sample in samples.items():
        pair = pairs.get(sample_id, {})
        row = {'sample_id': sample_id, 'article_url': sample['article_url'], 'image_url': sample['image_url'], 'caption': sample['context']['caption']}
        for mode in ['image_only', 'context_aware']:
            r = pair.get(mode, {})
            row[mode+'_output'] = r.get('description')
            row[mode+'_latency_ms'] = r.get('inference_ms')
            row[mode+'_error'] = json.dumps(r.get('error')) if r.get('error') else ('not_run' if not r else '')
        rows.append(row)
    with (directory/'review.csv').open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fields); writer.writeheader(); writer.writerows(rows)
    complete = sum(all(p.get(m, {}).get('status') == 'success' for m in ['image_only', 'context_aware']) for p in pairs.values())
    summary = [f'# Preliminary A/B run\n\nManifest examples: {len(samples)}. Recorded attempts: {len(records)}. Complete successful pairs: {complete}.',
               '\nHuman ratings are blank. No claim about factuality, relevance, accessibility benefit or statistical significance is supported yet.']
    for mode in ['image_only', 'context_aware']:
        subset = [r for r in records if r['mode'] == mode]; successes = [r for r in subset if r['status'] == 'success']
        values = [r['inference_ms'] for r in successes]
        summary.append(f'\n{mode}: {len(successes)}/{len(subset)} successful; median inference ' + (f'{statistics.median(values)/1000:.2f} seconds.' if values else 'unavailable.'))
    (directory/'summary.md').write_text('\n'.join(summary))
    cards = []
    for row in rows:
        sid = row['sample_id']; sample = samples[sid]
        esc = lambda x: html.escape(str(x or 'Unavailable'))
        cards.append(f"<article><h2>{esc(sid)} — {esc(sample['context']['article_title'])}</h2><a href='{esc(sample['article_url'])}'>Source article</a><p>Caption: {esc(row['caption'])}</p><div class='pair'><section><h3>Image only</h3><p>{esc(row['image_only_output'])}</p><p>{esc(row['image_only_error'])}</p></section><section><h3>Context aware</h3><p>{esc(row['context_aware_output'])}</p><p>{esc(row['context_aware_error'])}</p></section></div></article>")
    (directory/'comparison.html').write_text("<!doctype html><html lang='en'><meta charset='utf-8'><title>Pilot comparison</title><style>body{font:18px/1.6 system-ui;max-width:1000px;margin:auto;padding:20px}.pair{display:grid;grid-template-columns:1fr 1fr;gap:24px}article{border-bottom:1px solid #aaa;padding:20px 0}@media(max-width:600px){.pair{grid-template-columns:1fr}}</style><h1>Actual pilot generations</h1><p>Unreviewed model outputs. Ratings remain blank; this pilot does not establish accessibility benefit.</p>" + ''.join(cards) + '</html>')
    print('\n'.join(summary))

if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('--manifest', default='benchmark/manifests/pilot.jsonl'); p.add_argument('--runs', default='artifacts/runs/pilot.jsonl'); p.add_argument('--output', default='artifacts/results/pilot')
    a = p.parse_args(); analyze(a.manifest, a.runs, a.output)
