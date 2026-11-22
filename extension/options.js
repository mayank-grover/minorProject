const field = document.querySelector('#token');
chrome.storage.local.get('token').then(({token}) => { field.value = token || ''; });
document.querySelector('#settings').addEventListener('submit', async event => {
  event.preventDefault(); await chrome.storage.local.set({token: field.value.trim()});
  document.querySelector('#status').textContent = 'Token saved. Start the backend, then activate the extension on Wikipedia.';
});

document.querySelector('#test-connection')?.addEventListener('click', async () => {
  const status = document.querySelector('#status');
  status.textContent = 'Connecting to http://127.0.0.1:8000/health...';
  try {
    const res = await fetch('http://127.0.0.1:8000/health');
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    status.textContent = `Backend online! Model: ${data.model_id} (${data.status}).`;
  } catch (err) {
    status.textContent = `Connection failed: ${err.message}. Make sure FastAPI is running.`;
  }
});
