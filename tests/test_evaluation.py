import json
from pathlib import Path
from PIL import Image
from backend.data.images import prepare_image
from benchmark.run import run
from benchmark.analyze import analyze

def test_paired_logging_resume_and_blank_reviews(tmp_path, fake_model):
    image_path = tmp_path/'image.png'; Image.new('RGB', (64,64), 'red').save(image_path)
    _, _, digest, _ = prepare_image(image_path.read_bytes())
    manifest = tmp_path/'manifest.jsonl'; output = tmp_path/'runs.jsonl'
    manifest.write_text(json.dumps({'sample_id': 'pilot-1', 'image_hash': digest, 'local_image': str(image_path),
        'article_url': 'https://en.wikipedia.org/wiki/Test', 'image_url': 'https://upload.wikimedia.org/wikipedia/test.png',
        'context': {'article_title': 'CANARY-TITLE', 'caption': 'CANARY-CAPTION'}})+'\n')
    run(manifest, output, fake_model); run(manifest, output, fake_model)
    rows = [json.loads(line) for line in output.read_text().splitlines()]
    assert len(rows) == 2
    assert [r['mode'] for r in rows] == ['image_only', 'context_aware']
    assert all(r['status'] == 'success' and r['model_id'] == 'unit-test-fixture' for r in rows)
    assert 'CANARY' not in rows[0]['prompt']
    analyze(manifest, output, tmp_path/'report')
    import csv
    review = list(csv.DictReader((tmp_path/'report/review.csv').open()))
    assert review[0]['image_only_visual_factuality'] == ''
    assert review[0]['reviewer_id'] == ''
    assert 'Complete successful pairs: 1' in (tmp_path/'report/summary.md').read_text()
    # Failure remains in the run matrix and reporting denominator.
    fake_model.generate = lambda *args: (_ for _ in ()).throw(RuntimeError('failure'))
    failed = tmp_path/'failed.jsonl'; run(manifest, failed, fake_model)
    assert all(json.loads(x)['status'] == 'failed' for x in failed.read_text().splitlines())
