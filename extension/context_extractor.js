/* Person 1: bounded, occurrence-specific snapshots; no page modifications. */
(() => {
  const clean = (el, max) => {
    if (!el) return null;
    const copy = el.cloneNode(true);
    copy.querySelectorAll('[data-wiki-description-control]').forEach(node => node.remove());
    return copy.textContent.replace(/\[\d+\]/g, '').replace(/\s+/g, ' ').trim().slice(0, max);
  };
  const supported = () => location.hostname === 'en.wikipedia.org' && location.pathname.startsWith('/wiki/') &&
    !decodeURIComponent(location.pathname.slice(6)).includes(':') &&
    !new URLSearchParams(location.search).has('action') && !new URLSearchParams(location.search).has('diff');
  const root = () => document.querySelector('#mw-content-text .mw-parser-output') || document.querySelector('#mw-content-text');
  const eligible = () => {
    if (!supported() || !root()) return [];
    return Array.from(root().querySelectorAll('img')).filter(img => {
      let url;
      try { url = new URL(img.currentSrc || img.src, location.href); } catch { return false; }
      return url.protocol === 'https:' && ['upload.wikimedia.org', 'thumb.wikimedia.org'].includes(url.hostname) &&
        !img.closest('.navbox,.vertical-navbox,.metadata,.ambox,.sistersitebox,.mw-editsection,.noprint,.haudio,.mw-indicators') &&
        !/(?:icon|logo|flagicon|badge)/i.test(img.className) &&
        (img.naturalWidth || Number(img.getAttribute('width')) || 0) >= 32 &&
        (img.naturalHeight || Number(img.getAttribute('height')) || 0) >= 32;
    });
  };
  const occurrences = new WeakMap();
  function extract(img, index) {
    if (!occurrences.has(img)) occurrences.set(img, crypto.randomUUID());
    const article = root();
    if (!article || !img.isConnected) throw new Error('Image is no longer on this article.');
    const container = img.closest('.gallerybox') || img.closest('figure,.thumb') || img.closest('td') || img.parentElement;
    let caption = container.querySelector('figcaption,.thumbcaption,.gallerytext');
    if (!caption && img.closest('.infobox')) {
      // Only an explicitly marked caption in the image's own row may be associated.
      caption = img.closest('tr')?.querySelector('.infobox-caption');
    }
    let captionText = clean(caption, 1200);
    if (captionText === null && img.closest('.infobox')) {
      const row = img.closest('tr');
      // Associated text comes only from this image's own row, not other images' rows.
      const rowText = clean(row, 900);
      if (rowText) {
        const label = clean(row?.previousElementSibling?.querySelector('th'), 250);
        captionText = label ? `${label}: ${rowText}` : rowText;
      }
    }
    const blocks = Array.from(article.querySelectorAll('h2,h3,h4,p'))
      .filter(el => !el.closest('.navbox,.metadata,.ambox,.infobox,.reflist,figure,.thumb,.gallerybox'));
    let section = null;
    let preceding = null;
    let following = null;
    for (const block of blocks) {
      const before = !!(block.compareDocumentPosition(img) & Node.DOCUMENT_POSITION_FOLLOWING);
      if (before) {
        if (/^H/.test(block.tagName)) { section = block; preceding = null; }
        else if (clean(block, 1600)) preceding = block;
      } else {
        if (/^H/.test(block.tagName)) break;
        if (clean(block, 1600)) { following = block; break; }
      }
    }
    const nearby = [clean(preceding, 1600), clean(following, 1600)].filter(Boolean).join(' ').split(/\s+/).slice(0, 240).join(' ');
    const title = clean(document.querySelector('#firstHeading'), 300) || document.title.replace(/ - Wikipedia$/, '').slice(0, 300);
    return {
      schema_version: '1.0', request_id: crypto.randomUUID(), occurrence_id: occurrences.get(img),
      article_url: `${location.origin}${location.pathname}`,
      revision_id: Number(document.querySelector('meta[property="mw:revisionId"]')?.content) || null,
      image_url: img.currentSrc || img.src,
      context: {article_title: title, caption: captionText, section_heading: clean(section, 300),
        nearby_text: nearby || null, existing_alt: img.hasAttribute('alt') ? img.getAttribute('alt').slice(0, 600) : null},
      mode: 'context_aware', detail: 'concise'
    };
  }
  globalThis.WikiContext = {eligible, extract, supported};
})();
