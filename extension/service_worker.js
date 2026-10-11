/* Person 4: network requests stay in MV3's privileged worker. */
chrome.action.onClicked.addListener(tab => {
  if (!tab.id || !tab.url?.startsWith('https://en.wikipedia.org/wiki/')) return;
  chrome.tabs.sendMessage(tab.id, {type: 'TOGGLE'}).catch(() => {});
});
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type !== 'DESCRIBE') return false;
  if (!sender.tab?.url?.startsWith('https://en.wikipedia.org/wiki/')) {
    sendResponse({error: 'Requests must originate from a Wikipedia article.'}); return false;
  }
  (async () => {
    const {token = ''} = await chrome.storage.local.get('token');
    if (!token) throw new Error('Open extension options and enter the local backend token first.');
    const request = message.payload;
    const imageURL = new URL(request.image_url);
    if (imageURL.protocol !== 'https:' || !['upload.wikimedia.org', 'thumb.wikimedia.org'].includes(imageURL.hostname) || imageURL.username || imageURL.password) {
      throw new Error('Only Wikimedia image URLs are supported.');
    }
    // Passing bytes avoids making the model/provider fetch a URL. Credentials are never sent.
    const imageResponse = await fetch(imageURL.href, {credentials: 'omit', redirect: 'error', signal: AbortSignal.timeout(15000)});
    if (!imageResponse.ok) throw new Error(`Wikimedia image fetch failed (${imageResponse.status}).`);
    const max = 8 * 1024 * 1024;
    if (Number(imageResponse.headers.get('content-length')) > max) throw new Error('Image exceeds 8 MB. Choose a thumbnail.');
    const reader = imageResponse.body.getReader();
    const chunks = []; let total = 0;
    while (true) {
      const {value, done} = await reader.read(); if (done) break;
      total += value.length;
      if (total > max) { await reader.cancel(); throw new Error('Image exceeds 8 MB.'); }
      chunks.push(value);
    }
    const bytes = new Uint8Array(total); let offset = 0;
    for (const chunk of chunks) { bytes.set(chunk, offset); offset += chunk.length; }
    let binary = '';
    for (let i = 0; i < bytes.length; i += 8192) binary += String.fromCharCode(...bytes.subarray(i, i + 8192));
    request.image_base64 = btoa(binary);
    const response = await fetch('http://127.0.0.1:8000/describe', {
      method: 'POST', headers: {'Content-Type': 'application/json', 'Authorization': `Bearer ${token}`},
      body: JSON.stringify(request), signal: AbortSignal.timeout(130000)
    });
    const result = await response.json();
    if (!response.ok) throw new Error(result.error?.message || `Backend returned ${response.status}.`);
    sendResponse({result});
  })().catch(error => sendResponse({error: error.message || 'Request failed. Check backend setup.'}));
  return true;
});
