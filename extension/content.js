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
  function finishSpeech(session, statusText) {
    if (narration !== session) return;
    narration = null;
    if (session.player) {
      session.player.pause();
      session.player.removeAttribute('src');
      session.player.load();
    }
    if (session.objectURL) URL.revokeObjectURL(session.objectURL);
    session.read.textContent = 'Read aloud';
    session.read.setAttribute('aria-pressed', 'false');
    if (document.activeElement === session.pause) session.read.focus();
    session.pause.hidden = true;
    session.pause.textContent = 'Pause reading';
    if (statusText) session.item.status.textContent = statusText;
  }
  function stopSpeech() {
    if (!narration) return;
    const session = narration;
    // Clear our state before cancel; a delayed end/error must not reset a newer reading.
    finishSpeech(session, 'Reading stopped.');
    window.speechSynthesis?.cancel();
  }
  const KOKORO_VOICES = [
    ['kokoro:af_heart', 'Kokoro English — US, Heart'], ['kokoro:af_bella', 'Kokoro English — US, Bella'],
    ['kokoro:af_sarah', 'Kokoro English — US, Sarah'], ['kokoro:af_nicole', 'Kokoro English — US, Nicole'],
    ['kokoro:af_sky', 'Kokoro English — US, Sky'], ['kokoro:am_adam', 'Kokoro English — US, Adam'],
    ['kokoro:am_michael', 'Kokoro English — US, Michael'], ['kokoro:bf_emma', 'Kokoro English — UK, Emma'],
    ['kokoro:bf_isabella', 'Kokoro English — UK, Isabella'], ['kokoro:bm_george', 'Kokoro English — UK, George'],
    ['kokoro:bm_lewis', 'Kokoro English — UK, Lewis']
  ];
  const BOSON_VOICES = [
    ['boson:default', 'Boson cloud — Auto'], ['boson:eleanor', 'Boson cloud — Eleanor'],
    ['boson:oliver', 'Boson cloud — Oliver'], ['boson:chloe', 'Boson cloud — Chloe'],
    ['boson:nora', 'Boson cloud — Nora'], ['boson:marcus', 'Boson cloud — Marcus'], ['boson:jake', 'Boson cloud — Jake']
  ];
  function speechCompletionStatus(session) {
    const action = session.preview ? 'Voice preview finished' : 'Description read aloud';
    const voice = session.provider === 'boson' ? 'Boson cloud voice' : session.provider === 'kokoro' ? 'Kokoro voice' : 'device voice';
    return `${action} with the ${voice}.${session.fallbackReason ? ' Natural voice was unavailable.' : ''}`;
  }
  function startSystemSpeech(session, text, speed) {
    if (!window.speechSynthesis || !window.SpeechSynthesisUtterance) {
      finishSpeech(session, 'Speech synthesis is unavailable in this browser.');
      return;
    }
    const utterance = new SpeechSynthesisUtterance(text);
    const language = session.item.language?.value || 'en';
    const languagePattern = language === 'hi' ? /^hi(?:-|_)/i : /^en(?:-|_)/i;
    const voices = window.speechSynthesis.getVoices().filter(v => v.localService && languagePattern.test(v.lang));
    const preferredLocale = language === 'hi' ? 'hi-IN' : 'en-US';
    const score = v => (/enhanced|premium|natural/i.test(v.name) ? 4 : 0) + (v.default ? 2 : 0) + (new RegExp('^' + preferredLocale.replace('-', '[-_]') + '$', 'i').test(v.lang) ? 1 : 0);
    voices.sort((a, b) => score(b) - score(a));
    if (voices[0]) utterance.voice = voices[0];
    utterance.lang = voices[0]?.lang || (language === 'hi' ? 'hi-IN' : 'en-US');
    utterance.rate = speed; utterance.pitch = 1; utterance.volume = 1;
    session.kind = 'system'; session.provider = 'system'; session.utterance = utterance;
    session.pause.hidden = false;
    utterance.onend = () => finishSpeech(session, speechCompletionStatus(session));
    utterance.onerror = event => {
      if (narration !== session) return;
      finishSpeech(session, ['canceled', 'interrupted'].includes(event.error) ? 'Reading stopped.' : 'System voice playback failed. Check your device speech settings.');
    };
    try {
      if (window.speechSynthesis.paused) window.speechSynthesis.resume();
      window.speechSynthesis.speak(utterance);
      session.item.status.textContent = session.preview ? 'Playing voice preview with the device voice.' : 'Reading description with the device voice.';
    } catch {
      finishSpeech(session, 'System voice playback failed. Try Read aloud again.');
    }
  }
  async function startSpeech(item, read, pause, text, voice, speed, preview = false) {
    if (narration?.item === item) { stopSpeech(); return; }
    if (item.resultLanguage && item.resultLanguage !== item.language.value) {
      item.status.textContent = 'Language changed. Request a fresh description before reading it aloud.';
      return;
    }
    const speechLanguage = item.resultLanguage || item.language.value;
    const [provider, voiceName] = voice.includes(':') ? voice.split(':', 2) : [voice === 'system' ? 'system' : 'kokoro', voice];
    if (provider === 'kokoro' && speechLanguage === 'hi') {
      item.status.textContent = 'Kokoro voices are English. Choose a Boson voice or an available Hindi device voice.';
      return;
    }
    stopSpeech();
    const session = {item, read, pause, kind: provider, provider, preview};
    narration = session;
    read.textContent = 'Stop reading'; read.setAttribute('aria-pressed', 'true');
    pause.hidden = true; pause.textContent = 'Pause reading';
    if (provider === 'system') { startSystemSpeech(session, text, speed); return; }
    item.status.textContent = provider === 'boson' ? 'Preparing Boson cloud voice…' : 'Preparing local Kokoro voice…';
    try {
      const result = await chrome.runtime.sendMessage({type: 'SYNTHESIZE', payload: {
        text, provider, voice: voiceName, speed, language: speechLanguage,
      }});
      if (narration !== session) return;
      if (result?.error) throw new Error(result.error);
      if (!result?.audio_base64) throw new Error('Speech service returned no audio.');
      const binary = atob(result.audio_base64);
      const bytes = new Uint8Array(binary.length);
      for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
      session.objectURL = URL.createObjectURL(new Blob([bytes], {type: result.content_type || 'audio/wav'}));
      session.player = new Audio(session.objectURL);
      session.kind = 'audio';
      session.player.onended = () => finishSpeech(session, speechCompletionStatus(session));
      session.player.onerror = () => {
        if (narration === session) finishSpeech(session, 'Natural voice playback failed. Try the system voice.');
      };
      await session.player.play();
      if (narration === session) {
        pause.hidden = false;
        item.status.textContent = session.preview ? 'Playing voice preview with the natural voice.' : 'Reading description with the natural voice.';
      }
    } catch (error) {
      if (narration !== session) return;
      if (session.player) {
        const message = error.name === 'NotAllowedError'
          ? 'Chrome blocked natural-audio autoplay. Click Preview voice or Read aloud again, or choose Device voice.'
          : `Natural audio could not be played (${error.message}). Choose Device voice to use the fallback.`;
        finishSpeech(session, message);
        return;
      }
      session.fallbackReason = error.message;
      item.status.textContent = `${provider === 'boson' ? 'Boson cloud voice' : 'Kokoro voice'} unavailable (${error.message}). Using your device voice.`;
      startSystemSpeech(session, text, speed);
    }
  }
  function speechControls(item) {
    const voiceLabel = el('label', 'Narration voice ');
    const voice = el('select', '', {'aria-label': 'Narration voice'});
    for (const [value, label] of [...KOKORO_VOICES, ...BOSON_VOICES, ['system', 'Device voice']]) {
      voice.append(el('option', label, {value}));
    }
    if ((item.resultLanguage || item.language.value) === 'hi') voice.value = 'boson:default';
    voiceLabel.append(voice);
    const speedLabel = el('label', 'Speed ');
    const speed = el('input', '', {type: 'range', min: '0.8', max: '1.2', step: '0.05', value: '1', 'aria-label': 'Narration speed'});
    const speedValue = el('span', '1.00×');
    speed.addEventListener('input', () => { speedValue.textContent = `${Number(speed.value).toFixed(2)}×`; });
    speedLabel.append(speed, speedValue);
    const preview = button('Preview voice', () => startSpeech(item, read, pause,
      item.language.value === 'hi' ? 'यह आवाज़ का एक नमूना है।' : 'Here is a preview of this reading voice.',
      voice.value, Number(speed.value), true));
    const settings = el('div', '', {class: 'wiki-speech-settings'});
    settings.append(voiceLabel, speedLabel, preview);
    const read = button('Read aloud', () => startSpeech(
      item, read, pause, item.result.querySelector('.description').textContent, voice.value, Number(speed.value),
    ));
    read.setAttribute('aria-controls', item.result.id);
    read.setAttribute('aria-pressed', 'false');
    const pause = button('Pause reading', () => {
      if (narration?.item !== item) return;
      if (pause.textContent === 'Pause reading') {
        if (narration.kind === 'audio') narration.player?.pause();
        else window.speechSynthesis.pause();
        pause.textContent = 'Resume reading';
      } else {
        if (narration.kind === 'audio') narration.player?.play().catch(() => {});
        else window.speechSynthesis.resume();
        pause.textContent = 'Pause reading';
      }
    });
    pause.hidden = true;
    return [settings, read, pause];
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
    try { payload = WikiContext.extract(img, index); payload.detail = detail; payload.image_type = item.type.value; payload.language = item.language.value; }
    catch (error) { active.pending = false; status.textContent = error.message; return; }
    const snapshot = JSON.stringify({...payload, request_id: null});
    status.textContent = 'Generating description. This can take up to two minutes.';
    result.hidden = true; controls.replaceChildren(button('Cancel request', () => {
      generation++; active.pending = false; status.textContent = 'Request cancelled. Model may finish in the background.'; controls.replaceChildren();
    }));
    try {
      const response = await chrome.runtime.sendMessage({type: 'DESCRIBE', payload});
      if (id !== generation || !enabled || !img.isConnected || location.href !== url) return;
      const current = WikiContext.extract(img, index); current.detail = detail; current.image_type = item.type.value; current.language = item.language.value;
      if (JSON.stringify({...current, request_id: null}) !== snapshot) {
        active.pending = false; status.textContent = 'Image or article context changed. Please request a fresh description.'; controls.replaceChildren(); return;
      }
      if (response?.error) throw new Error(response.error);
      const data = response?.result;
      if (!data?.description?.trim()) throw new Error('Backend returned an empty description.');
      if (data.request_id !== payload.request_id || data.occurrence_id !== payload.occurrence_id) throw new Error('Response does not match this image. Retry.');
      active.pending = false;
      item.resultLanguage = data.language || payload.language;
      heading.textContent = `AI-generated description for image ${index + 1}`;
      result.querySelector('.description').textContent = data.description;
      result.querySelector('.metadata').textContent = `${data.model_id} · ${(data.inference_ms / 1000).toFixed(1)} s inference · ${data.language === 'hi' ? 'Hindi' : 'English'}${data.image_type ? ' · ' + data.image_type + ' description' : ''}`;
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
      const languageID = `wiki-description-language-${crypto.randomUUID()}`;
      const language = el('select', '', {id:languageID});
      language.append(el('option', 'English', {value:'en'}), el('option', 'Hindi', {value:'hi'}));
      const languageLabel = el('label', 'Language ', {for:languageID});
      languageLabel.append(language);
      const resultID = `wiki-description-result-${crypto.randomUUID()}`;
      const surface = el('div', '', {class: 'wiki-description-surface', hidden: ''});
      const status = el('p', '', {role: 'status', 'aria-live': 'polite', 'aria-atomic': 'true'});
      const controls = el('div');
      const result = el('section', '', {id: resultID, 'aria-labelledby': resultID + '-heading', hidden: ''});
      const heading = el('h3', '', {id: resultID + '-heading', tabindex: '-1'});
      result.append(heading, el('p', '', {class: 'description'}), el('p', '', {class: 'metadata'}), el('p', '', {class: 'limitations'}));
      surface.append(status, controls, result);
      const trigger = button(`Describe ${name}`, () => describe(img, WikiContext.eligible().indexOf(img), trigger));
      trigger.classList.add('primary-describe');
      trigger.setAttribute('aria-controls', resultID);
      wrapper.append(trigger, typeLabel, languageLabel, surface);
      const link = img.closest('a'); (link || img).after(wrapper);
      registered.set(img, {wrapper, trigger, surface, status, controls, result, heading, type, language});
    });
    list.replaceChildren(...images.map((img, index) => button(`Go to image ${index + 1}`, () => {
      const trigger = registered.get(img).trigger; trigger.scrollIntoView({block: 'center'}); trigger.focus();
    })));
    if (!images.length) list.append(el('p', 'No supported content images found on this article.'));
  }
  function enable() {
    if (!WikiContext.supported()) return;
    enabled = true; pageURL = location.href;
    window.speechSynthesis?.getVoices(); // Trigger asynchronous system voice discovery.
    panel = el('section', '', {id: 'wiki-description-panel', 'aria-labelledby': 'wiki-description-title'});
    const style = el('style'); style.textContent = `
      #wiki-description-panel {
        box-sizing:border-box;background:#f8fafc;color:#0f172a;
        border:1px solid #cbd5e1;border-radius:12px;box-shadow:0 4px 6px -1px rgba(0,0,0,0.05);
        padding:20px;margin:20px 0;font:1rem/1.6 system-ui,-apple-system,sans-serif;
      }
      #wiki-description-panel h2 {font-size:1.35rem;font-weight:700;color:#1e293b;margin-top:0;display:flex;align-items:center;gap:8px;}
      #wiki-description-panel button, [data-wiki-description-control] button {
        background:#ffffff;color:#1e293b;border:1px solid #cbd5e1;border-radius:8px;
        padding:8px 16px;margin:4px;font-weight:500;font-size:0.92rem;cursor:pointer;
        box-shadow:0 1px 2px rgba(0,0,0,0.05);transition:all 0.15s ease-in-out;
      }
      #wiki-description-panel button:hover, [data-wiki-description-control] button:hover {
        background:#f1f5f9;border-color:#94a3b8;transform:translateY(-1px);box-shadow:0 2px 4px rgba(0,0,0,0.08);
      }
      [data-wiki-description-control] button.primary-describe {
        background:#2563eb;color:#ffffff;border:none;box-shadow:0 2px 4px rgba(37,99,235,0.25);
      }
      [data-wiki-description-control] button.primary-describe:hover {
        background:#1d4ed8;box-shadow:0 4px 6px rgba(37,99,235,0.35);
      }
      #wiki-description-panel :focus-visible, [data-wiki-description-control] :focus-visible {
        outline:3px solid #3b82f6;outline-offset:2px;
      }
      #wiki-description-panel [hidden], [data-wiki-description-control] [hidden] {display:none !important;}
      [data-wiki-description-control] {display:block;max-width:100%;margin:10px 0;font-family:system-ui,-apple-system,sans-serif;}
      .wiki-description-surface {
        background:#ffffff;color:#0f172a;border:1px solid #e2e8f0;border-radius:10px;
        padding:16px;margin:10px 0;box-shadow:0 10px 15px -3px rgba(0,0,0,0.06);font-size:0.95rem;line-height:1.6;
        animation: fadeIn 0.25s ease-out;
      }
      @keyframes fadeIn { from { opacity: 0; transform: translateY(4px); } to { opacity: 1; transform: translateY(0); } }
      .wiki-description-surface h3 {font-size:1.05rem;font-weight:600;color:#0f172a;margin:4px 0 10px 0;}
      .wiki-description-surface .description {font-size:1rem;color:#334155;margin-bottom:12px;background:#f8fafc;padding:12px;border-radius:8px;border-left:4px solid #3b82f6;}
      .wiki-description-surface .metadata {font-size:0.82rem;color:#64748b;margin-bottom:6px;}
      .wiki-description-surface .limitations {font-size:0.82rem;color:#94a3b8;}
      .wiki-btn-group {display:flex;flex-wrap:wrap;gap:6px;margin:8px 0;}
      .wiki-speech-settings {display:flex;flex-wrap:wrap;align-items:center;gap:8px;margin:8px 4px;}
      .wiki-speech-settings label {display:inline-flex;align-items:center;gap:6px;font-size:0.88rem;}
      .wiki-speech-settings select, .wiki-speech-settings input {font:inherit;}
      .wiki-speech-settings select {max-width:15rem;padding:5px;border:1px solid #cbd5e1;border-radius:6px;background:#fff;color:#0f172a;}
      .wiki-speech-settings span {font-variant-numeric:tabular-nums;}
    `;
    panel.append(style, el('h2', 'Wikipedia image descriptions', {id: 'wiki-description-title', tabindex: '-1'}),
      el('p', 'Experimental AI descriptions. The selected public image, bounded article context, and optional narration text are sent to your local backend. Model assets may download from their upstream hosts on first use. Existing captions and alt text remain available.'),
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
