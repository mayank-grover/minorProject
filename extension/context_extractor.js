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
  function pageContext(article, img, title) {
    const blocks = [...article.querySelectorAll('h2,h3,p')].filter(el => !el.closest('.infobox,.navbox,.metadata,.ambox,.reflist,figure,.thumb,.gallerybox'));
    const firstHeading = blocks.find(el => el.matches('h2'));
    const lead = blocks.filter(el => el.matches('p') && (!firstHeading || (el.compareDocumentPosition(firstHeading) & Node.DOCUMENT_POSITION_FOLLOWING)) && (clean(el, 1000) || '').length > 60);
    const cards = [...article.querySelectorAll('.infobox.vcard')];
    const box = article.querySelector('.infobox.biography') || cards.find(card => [...card.querySelectorAll('th')].some(th => /^(?:Born|Birth name)$/i.test(clean(th,100) || '')));
    const biography = !!box;
    const subject = biography ? (clean(box.querySelector('.infobox-above,.fn'), 200) || title) : null;
    const aliases = [...new Set((lead[0] ? [...lead[0].querySelectorAll('b,strong')].map(el => clean(el,100)) : []).filter(Boolean))];
    if (box) {
      for (const row of box.querySelectorAll('tr')) {
        const label = clean(row.querySelector('th'), 100) || '';
        if (/^(?:Birth name|Born|Other names|Also known as)$/i.test(label)) {
          const cell = row.querySelector('td');
          const names = cell?.querySelectorAll('li').length ? [...cell.querySelectorAll('li')].map(el => clean(el,100)) : [clean(cell,100)?.split(/\(|\d/)[0].trim()];
          aliases.push(...names.filter(Boolean));
        }
      }
    }
    // Include major sections across the article before filling with subsections.
    const outline = [...blocks.filter(el => el.matches('h2')), ...blocks.filter(el => el.matches('h3'))].map(el => clean(el,80)).filter(Boolean).slice(0,12);
    const summaries = [];
    let heading = null;
    for (const block of blocks) {
      if (block.matches('h2')) heading = clean(block,70);
      else if (block.matches('p') && heading && summaries.length < 5) {
        const text = clean(block,140);
        if (text) summaries.push(`${heading}: ${text}`);
        heading = null;
      }
    }
    const images = eligible();
    const first = images[0];
    const main = box?.querySelector('.infobox-image img') || box?.querySelector('img');
    const beforeSections = !firstHeading || !!(img.compareDocumentPosition(firstHeading) & Node.DOCUMENT_POSITION_FOLLOWING);
    const role = img === main || (img === first && beforeSections) ? 'lead' : 'contextual';
    const inventory = [...article.querySelectorAll('figcaption,.thumbcaption,.gallerytext,.infobox-caption')].map(el => clean(el,90)).filter(Boolean).slice(0,8);
    return {page_summary:[clean(lead[0],650), ...summaries].filter(Boolean).join(' ').slice(0,1200),
      section_outline:outline, image_overview:inventory, article_kind:biography ? 'biography' : 'general',
      subject_name:subject, subject_aliases:[...new Set(aliases)].slice(0,8),
      image_position:images.indexOf(img), image_role:role, lead_subject_association:!!(subject && img === main)};
  }
  function associatedLabel(img, container) {
    // Country infoboxes often have separate flag/arms wrappers in the same cell.
    // Only use a nearby article link in a wrapper containing this image alone.
    for (let scope = img.parentElement; scope && container.contains(scope); scope = scope.parentElement) {
      if (scope.querySelectorAll('img').length !== 1) break;
      const copy = scope.cloneNode(true);
      copy.querySelectorAll('[data-wiki-description-control]').forEach(node => node.remove());
      const links = [...copy.querySelectorAll('a[href]')].filter(link => {
        const url = new URL(link.getAttribute('href'), location.href);
        return url.origin === location.origin && url.pathname.startsWith('/wiki/') &&
          !decodeURIComponent(url.pathname.slice(6)).includes(':') && !link.querySelector('img') && clean(link, 300);
      });
      if (links.length === 1) {
        const link = links[0];
        const title = link.getAttribute('title') || decodeURIComponent(new URL(link.getAttribute('href'), location.href).pathname.slice(6)).replace(/_/g, ' ');
        return title.replace(/\s+/g, ' ').trim().slice(0, 300);
      }
      if (scope === container) break;
    }
    return null;
  }
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
    let captionSubject = null;
    if (caption) {
      const link = caption.querySelector('a[href*="/wiki/"]');
      if (link && !new URL(link.href).pathname.includes(':')) {
        const prefix = clean(caption,1200).split(clean(link,200))[0].trim();
        if (/^(?:The|A|An)?$/i.test(prefix)) captionSubject = (prefix ? prefix + ' ' : '') + clean(link,180);
      }
    }
    if (!captionText) { captionText = associatedLabel(img, container); captionSubject = captionText; }
    if (captionText === null && img.closest('.infobox')) {
      const row = img.closest('tr');
      // Associated text comes only from this image's own row, not other images' rows.
      const rowText = row?.querySelectorAll('img').length === 1 ? clean(row, 900) : null;
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
    const nearby = [clean(preceding, 1000), clean(following, 1000)].filter(Boolean).join(' ').split(/\s+/).slice(0, 100).join(' ');
    const title = clean(document.querySelector('#firstHeading'), 300) || document.title.replace(/ - Wikipedia$/, '').slice(0, 300);
    return {
      schema_version: '1.0', request_id: crypto.randomUUID(), occurrence_id: occurrences.get(img),
      article_url: `${location.origin}${location.pathname}`,
      revision_id: Number(document.querySelector('meta[property="mw:revisionId"]')?.content) || null,
      image_url: img.currentSrc || img.src,
      context: {...pageContext(article,img,title), caption_subject:captionSubject,
        article_title: title, caption: captionText, section_heading: clean(section, 300),
        nearby_text: nearby || null, existing_alt: img.hasAttribute('alt') ? img.getAttribute('alt').slice(0, 600) : null},
      mode: 'context_aware', detail: 'concise'
    };
  }
  globalThis.WikiContext = {eligible, extract, supported};
})();
