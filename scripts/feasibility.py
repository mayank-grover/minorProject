"""One real image + a swapped visual fixture; outputs are saved, never simulated."""
import json
import platform
import time
from pathlib import Path
import httpx
from PIL import Image, ImageDraw
from backend.models.smolvlm import SmolVLM

Path('artifacts').mkdir(exist_ok=True)
model = SmolVLM(max_new_tokens=128)
start = time.perf_counter()
model.load()
load_s = time.perf_counter() - start
url = 'https://huggingface.co/datasets/huggingface/documentation-images/resolve/main/bee.jpg'
r = httpx.get(url, follow_redirects=True, timeout=60)
r.raise_for_status()
Path('artifacts/bee.jpg').write_bytes(r.content)
image = Image.open('artifacts/bee.jpg').convert('RGB')
image.thumbnail((768, 768))
prompt = 'Describe the visible image in plain English for a blind reader. Do not guess identities or unreadable text. Use 30 to 70 words.'
first = model.generate(image, prompt)
fixture = Image.new('RGB', (400, 400), 'white')
ImageDraw.Draw(fixture).rectangle((80, 80, 320, 320), fill='red')
fixture.save('artifacts/red-square.png')
second = model.generate(fixture, prompt)
report = {'hardware': 'Apple M2 / 16 GB RAM', 'platform': platform.platform(),
          'configuration': model.configuration(), 'load_seconds': load_s,
          'source': url, 'real_image': vars(first), 'swapped_fixture': vars(second)}
Path('artifacts/feasibility.json').write_text(json.dumps(report, indent=2))
print(json.dumps(report, indent=2))
