const field = document.querySelector('#token');
chrome.storage.local.get('token').then(({token}) => { field.value = token || ''; });
document.querySelector('#settings').addEventListener('submit', async event => {
  event.preventDefault(); await chrome.storage.local.set({token: field.value.trim()});
  document.querySelector('#status').textContent = 'Token saved. Start the backend, then activate the extension on Wikipedia.';
});
