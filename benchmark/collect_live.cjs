// Snapshot what the extension would send for real articles: runs extension/context_extractor.js
// on the live article HTML in jsdom. Occurrences are chosen by rule (first and middle eligible
// image), not by hand. Usage: node benchmark/collect_live.cjs out.jsonl Slug[=category] ...
const fs = require('node:fs');
const {JSDOM} = require('jsdom');
const UA = process.env.WIKIMEDIA_USER_AGENT || 'WikiImageAccessibility/0.1 (local student prototype)';
const extractor = fs.readFileSync('extension/context_extractor.js', 'utf8');

// srcset "url 1.5x, url 2x" -> {1: src, 1.5: url, 2: url}
function renditions(img) {
  const out = {'1': img.src};
  for (const part of (img.getAttribute('srcset') || '').split(',')) {
    const [url, scale] = part.trim().split(/\s+/);
    if (url && /x$/.test(scale || '')) out[scale.slice(0, -1)] = new URL(url, 'https://en.wikipedia.org').href;
  }
  return out;
}

async function collect(slug, category) {
  const url = `https://en.wikipedia.org/wiki/${slug}`;
  const html = await (await fetch(url, {headers: {'User-Agent': UA}})).text();
  if (process.env.HTML_DIR) { fs.mkdirSync(process.env.HTML_DIR, {recursive: true}); fs.writeFileSync(`${process.env.HTML_DIR}/${slug}.html`, html); }
  const dom = new JSDOM(html, {url, runScripts: 'outside-only'});
  const {window} = dom;
  window.eval(extractor);
  const images = window.WikiContext.eligible();
  const picks = [...new Set([0, Math.floor(images.length / 2)])].filter(i => i < images.length);
  const rows = picks.map(index => {
    const img = images[index];
    const payload = window.WikiContext.extract(img, index);
    delete payload.request_id; delete payload.occurrence_id;
    return {slug, category, index, eligible_count: images.length, payload, renditions: renditions(img),
      display_width: Number(img.getAttribute('width')) || null, retrieved_utc: new Date().toISOString()};
  });
  dom.window.close();
  return rows;
}

(async () => {
  const [out, ...specs] = process.argv.slice(2);
  const lines = [];
  for (const spec of specs) {
    const [slug, category = 'unspecified'] = spec.split('=');
    try {
      const rows = await collect(slug, category);
      rows.forEach(r => lines.push(JSON.stringify(r)));
      console.log(slug, rows.map(r => `#${r.index}/${r.eligible_count} w=${r.display_width}`).join(' '));
    } catch (error) {
      console.log('EXCLUDED', slug, error.message);
    }
    await new Promise(r => setTimeout(r, 500));
  }
  fs.writeFileSync(out, lines.join('\n') + '\n');
})();
