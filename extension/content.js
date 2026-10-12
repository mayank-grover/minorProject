/* Person 4: results and request controls stay beside their selected image. */
(() => {
  let enabled = false, panel, list, observer;
  let generation = 0, pageURL, active, opener;
  const registered = new Map();
  let narration;
  const el = (tag, text, attrs = {}) => {
    const node = document.createElement(tag); if (text) node.textContent = text;
    for (const [key, value] of Object.entries(attrs)) node.setAttribute(key, value);
    return node;
  };
  const button = (text, action) => { const node = el('button', text, {type: 'button'}); node.addEventListener('click', action); return node; };
  function finishSpeech(session) {
    if (narration !== session) return;
    narration = null;
    session.read.textContent = 'Read aloud';
    session.read.setAttribute('aria-pressed', 'false');
    if (document.activeElement === session.pause) session.read.focus();
    session.pause.hidden = true;
    session.pause.textContent = 'Pause reading';
  }
  function stopSpeech() {
    if (!narration) return;
    const session = narration;
    // Clear our state before cancel; a delayed end/error must not reset a newer reading.
    finishSpeech(session);
    window.speechSynthesis.cancel();
  }
  function speechControls(item) {
    const read = button('Read aloud', () => {
      if (narration?.item === item) { stopSpeech(); return; }
      if (!window.speechSynthesis || !window.SpeechSynthesisUtterance) {
        item.status.textContent = 'Read aloud is unavailable in this browser.'; return;
      }
      stopSpeech();
      const utterance = new SpeechSynthesisUtterance(item.result.querySelector('.description').textContent);
      // Prefer an English voice installed on the device. Enhanced voices get priority.
      const voices = window.speechSynthesis.getVoices().filter(v => v.localService && /^en(?:-|_)/i.test(v.lang));
      const score = v => (/enhanced|premium|natural/i.test(v.name) ? 4 : 0) + (v.default ? 2 : 0) + (/^en-US$/i.test(v.lang) ? 1 : 0);
      voices.sort((a, b) => score(b) - score(a));
      if (voices[0]) utterance.voice = voices[0];
      utterance.lang = voices[0]?.lang || 'en-US';
      utterance.rate = 0.95; utterance.pitch = 1; utterance.volume = 1;
      const session = {item, read, pause, utterance};
      narration = session;
      read.textContent = 'Stop reading'; read.setAttribute('aria-pressed', 'true');
      pause.hidden = false;
      utterance.onend = () => finishSpeech(session);
      utterance.onerror = event => {
        if (narration !== session) return;
        finishSpeech(session);
        if (!['canceled', 'interrupted'].includes(event.error)) item.status.textContent = 'Audio playback failed. Try Read aloud again or check your device speech settings.';
      };
      try {
        // Cancel does not necessarily clear the synthesizer's paused state.
        if (window.speechSynthesis.paused) window.speechSynthesis.resume();
        window.speechSynthesis.speak(utterance);
      }
      catch { finishSpeech(session); item.status.textContent = 'Audio playback failed. Try Read aloud again.'; }
    });
    read.setAttribute('aria-controls', item.result.id);
    read.setAttribute('aria-pressed', 'false');
    const pause = button('Pause reading', () => {
      if (narration?.item !== item) return;
      if (pause.textContent === 'Pause reading') {
        window.speechSynthesis.pause(); pause.textContent = 'Resume reading';
      } else {
        window.speechSynthesis.resume(); pause.textContent = 'Pause reading';
      }
    });
    pause.hidden = true;
    return [read, pause];
  }
  function disable() {
    stopSpeech();
    generation++; enabled = false; observer?.disconnect();
    for (const item of registered.values()) item.wrapper.remove();
    registered.clear(); panel?.remove(); panel = null;
    if (opener?.isConnected) opener.focus();
  }
  async function describe(img, index, trigger, detail = 'concise') {
    const item = registered.get(img);
    if (!item) return;
    if (narration?.item === item) stopSpeech();
    if (active?.pending) {
      active.item.status.textContent = 'Previous request superseded. Model may finish in the background.';
      active.item.controls.replaceChildren();
    }
    const {surface, status, result, heading, controls} = item;
    surface.hidden = false;
    const id = ++generation;
    const url = location.href;
    active = {img, index, trigger, item, pending: true}; opener = trigger;
    let payload;
    try { payload = WikiContext.extract(img, index); payload.detail = detail; payload.image_type = item.type.value; }
    catch (error) { active.pending = false; status.textContent = error.message; return; }
    const snapshot = JSON.stringify({...payload, request_id: null});
    status.textContent = 'Generating description. Local inference may take up to two minutes.';
    result.hidden = true; controls.replaceChildren(button('Cancel request', () => {
      generation++; active.pending = false; status.textContent = 'Request cancelled. Model may finish in the background.'; controls.replaceChildren();
    }));
    try {
      const response = await chrome.runtime.sendMessage({type: 'DESCRIBE', payload});
      if (id !== generation || !enabled || !img.isConnected || location.href !== url) return;
      const current = WikiContext.extract(img, index); current.detail = detail; current.image_type = item.type.value;
      if (JSON.stringify({...current, request_id: null}) !== snapshot) {
        active.pending = false; status.textContent = 'Image or article context changed. Please request a fresh description.'; controls.replaceChildren(); return;
      }
      if (response?.error) throw new Error(response.error);
      const data = response?.result;
      if (!data?.description?.trim()) throw new Error('Backend returned an empty description.');
      if (data.request_id !== payload.request_id || data.occurrence_id !== payload.occurrence_id) throw new Error('Response does not match this image. Retry.');
      active.pending = false;
      heading.textContent = `AI-generated description for image ${index + 1}`;
      result.querySelector('.description').textContent = data.description;
      result.querySelector('.metadata').textContent = `${data.model_id} · ${(data.inference_ms / 1000).toFixed(1)} s inference · Local processing${data.image_type ? ' · ' + data.image_type + ' description' : ''}`;
      result.querySelector('.limitations').textContent = data.limitations.join(' ');
      result.hidden = false;
      status.textContent = 'Description ready. Use Read description to move to the result.';
      controls.replaceChildren(button('Read description', () => { result.scrollIntoView({block: 'nearest'}); heading.focus(); }),
        ...speechControls(item),
        button(detail === 'concise' ? 'More detail' : 'Concise description', () => describe(img, index, trigger, detail === 'concise' ? 'detailed' : 'concise')),
        button('Refresh description', () => describe(img, index, trigger, detail)));
    } catch (error) {
      if (id !== generation || !enabled || location.href !== url || !img.isConnected) return;
      active.pending = false;
      status.textContent = `Description unavailable: ${error.message}`;
      controls.replaceChildren(button('Retry', () => describe(img, index, trigger, detail)));
    }
  }
  function scan() {
    if (!enabled) return;
    if (location.href !== pageURL || !WikiContext.supported()) { disable(); return; }
    const images = WikiContext.eligible();
    for (const [img, item] of registered) {
      if (!images.includes(img)) { if (narration?.item === item) stopSpeech(); item.wrapper.remove(); registered.delete(img); }
    }
    images.forEach((img, index) => {
      if (registered.has(img)) return;
      const snapshot = WikiContext.extract(img, index);
      const name = snapshot.context.caption?.slice(0, 80) || `image ${index + 1}`;
      const wrapper = el('div', '', {'data-wiki-description-control': ''});
      const typeID = `wiki-description-type-${crypto.randomUUID()}`;
      const type = el('select', '', {id:typeID});
      for (const [value, name] of [['auto','Automatic'], ['photo','Photo'], ['flag','Flag'], ['chart','Chart'], ['map','Map'], ['process','Process or lifecycle'], ['diagram','Other diagram']]) {
        type.append(el('option', name, {value}));
      }
      const typeLabel = el('label', 'Description style ', {for:typeID});
      typeLabel.append(type);
      const resultID = `wiki-description-result-${crypto.randomUUID()}`;
      const surface = el('div', '', {class: 'wiki-description-surface', hidden: ''});
      const status = el('p', '', {role: 'status', 'aria-live': 'polite', 'aria-atomic': 'true'});
      const controls = el('div');
      const result = el('section', '', {id: resultID, 'aria-labelledby': resultID + '-heading', hidden: ''});
      const heading = el('h3', '', {id: resultID + '-heading', tabindex: '-1'});
      result.append(heading, el('p', '', {class: 'description'}), el('p', '', {class: 'metadata'}), el('p', '', {class: 'limitations'}));
      surface.append(status, controls, result);
      const trigger = button(`Describe ${name}`, () => describe(img, WikiContext.eligible().indexOf(img), trigger));
      trigger.setAttribute('aria-controls', resultID);
      wrapper.append(trigger, typeLabel, surface);
      const link = img.closest('a'); (link || img).after(wrapper);
      registered.set(img, {wrapper, trigger, surface, status, controls, result, heading, type});
    });
    list.replaceChildren(...images.map((img, index) => button(`Go to image ${index + 1}`, () => {
      const trigger = registered.get(img).trigger; trigger.scrollIntoView({block: 'center'}); trigger.focus();
    })));
    if (!images.length) list.append(el('p', 'No supported content images found on this article.'));
  }
  function enable() {
    if (!WikiContext.supported()) return;
    enabled = true; pageURL = location.href;
    window.speechSynthesis?.getVoices(); // Trigger asynchronous voice discovery before first playback.
    panel = el('section', '', {id: 'wiki-description-panel', 'aria-labelledby': 'wiki-description-title'});
    const style = el('style'); style.textContent = `
      #wiki-description-panel {box-sizing:border-box;background:#fff;color:#17202a;border:2px solid #364c67;padding:16px;margin:16px 0;font:1rem/1.5 sans-serif;overflow-wrap:anywhere;}
      #wiki-description-panel button,[data-wiki-description-control] button {background:#f1f5fa;color:#17202a;border:1px solid #425c7a;border-radius:4px;padding:8px 12px;margin:4px;white-space:normal;font:inherit;cursor:pointer;}
      #wiki-description-panel :focus-visible,[data-wiki-description-control] :focus-visible {outline:3px solid #005fcc;outline-offset:3px;}
      #wiki-description-panel [hidden],[data-wiki-description-control] [hidden] {display:none;}
      [data-wiki-description-control] {display:block;max-width:100%;box-sizing:border-box;white-space:normal;text-align:left;}
      .wiki-description-surface {background:#fff;color:#17202a;border:1px solid #425c7a;border-radius:4px;padding:12px;margin:8px 0;overflow-wrap:anywhere;font:1rem/1.5 sans-serif;}
      .wiki-description-surface h3 {font-size:1.1rem;margin:8px 0;}
      .wiki-description-surface .metadata,.wiki-description-surface .limitations {font-size:.85rem;}
    `;
    panel.append(style, el('h2', 'Wikipedia image descriptions', {id: 'wiki-description-title', tabindex: '-1'}),
      el('p', 'Experimental AI descriptions. The selected public image and bounded article context are sent to your local backend. Existing captions and alt text remain available.'),
      button('Disable for this page', disable));
    list = el('div', '', {'aria-label': 'Article image controls'});
    panel.append(el('p', 'Choose a Describe button beside an image. Its result will appear there.'), list);
    document.querySelector('#mw-content-text')?.before(panel);
    scan();
    let scheduled = false;
    observer = new MutationObserver(mutations => {
      if (mutations.every(m => m.target.closest?.('#wiki-description-panel,[data-wiki-description-control]'))) return;
      if (!scheduled) { scheduled = true; setTimeout(() => { scheduled = false; scan(); }, 250); }
    });
    observer.observe(document.querySelector('#mw-content-text'), {childList: true, subtree: true, attributes: true, attributeFilter: ['src', 'srcset', 'alt']});
    panel.querySelector('h2').focus();
  }
  chrome.runtime.onMessage.addListener(message => { if (message.type === 'TOGGLE') enabled ? disable() : enable(); });
  window.addEventListener('popstate', () => { if (enabled && location.href !== pageURL) disable(); });
  window.addEventListener('pagehide', stopSpeech);
  document.addEventListener('keydown', event => {
    if (event.key === 'Escape' && enabled) {
      const item = [...registered.values()].find(item => item.surface.contains(document.activeElement));
      const target = item?.trigger || (panel?.contains(document.activeElement) ? active?.trigger : null);
      if (target?.isConnected) target.focus();
    }
  });
})();
