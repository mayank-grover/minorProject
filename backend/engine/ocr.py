"""Bounded local Tesseract OCR; no cloud calls or model-generated OCR text."""
import csv
import io
from pathlib import Path
import shutil
import subprocess
import tempfile
import time


class LocalOCR:
    def __init__(self):
        self.command = None
        self.engine = 'unavailable'
        self.problem = 'Install Tesseract with English language data to enable local OCR.'

    def load(self):
        executable = shutil.which('tesseract')
        if not executable:
            executable = next((str(p) for p in [Path('/opt/homebrew/bin/tesseract'), Path('/usr/local/bin/tesseract')] if p.is_file()), None)
        if executable:
            self.command = [executable]
            self.engine = 'tesseract'

    def extract(self, image):
        start = time.perf_counter()
        if not self.command:
            return {'status':'unavailable', 'engine':self.engine, 'lines':[], 'ms':0, 'message':self.problem}
        try:
            with tempfile.TemporaryDirectory(prefix='wiki-ocr-') as directory:
                path = Path(directory) / 'image.png'
                image.save(path, format='PNG')
                lines = []
                # Sparse labels and boxed/aligned text need different segmentation.
                # Keep word positions: a chart's numeric value must not be merged
                # into a single line spanning several unrelated columns.
                for mode in ('11', '6'):
                    command = self.command + [str(path), 'stdout', '-l', 'eng', '--psm', mode, 'tsv']
                    output = subprocess.run(command, capture_output=True, check=True, timeout=7)
                    if len(output.stdout) > 500_000: raise ValueError('Oversized OCR result')
                    for row in csv.DictReader(io.StringIO(output.stdout.decode()), delimiter='\t'):
                        text = row['text'].strip()
                        confidence = float(row['conf']) / 100
                        if not text or confidence < .5: continue
                        left,top,width,height = [int(row[k]) for k in ('left','top','width','height')]
                        box=[left/image.width,top/image.height,width/image.width,height/image.height]
                        if len(text) == 1 and box[3] > .3: continue
                        if any(old['text'].casefold()==text.casefold() and abs(old['box'][0]-box[0])<.03 and abs(old['box'][1]-box[1])<.03 for old in lines): continue
                        lines.append({'text':text, 'confidence':confidence, 'box':box})
            lines = bound_lines(lines)
            return {'status':'ok' if lines else 'no_text', 'engine':self.engine,
                    'lines':lines, 'ms':(time.perf_counter()-start)*1000}
        except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError):
            return {'status':'failed', 'engine':self.engine, 'lines':[],
                    'ms':(time.perf_counter()-start)*1000, 'message':'Local OCR failed or exceeded its deadline.'}


def bound_lines(lines):
    accepted = []
    budget = 1200
    for line in sorted(lines, key=lambda item: (item['box'][1], item['box'][0])):
        text = ' '.join(str(line['text']).split())
        box = line['box']
        if float(line['confidence']) < .5 or not text or len(box) != 4: continue
        if any(not 0 <= float(value) <= 1 for value in box): continue
        if len(text) > budget or len(accepted) >= 16: break
        accepted.append({'text':text, 'box':[round(float(v),3) for v in box]})
        budget -= len(text)
    return accepted
