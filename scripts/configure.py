"""Create local settings without leaking tokens or replacing existing credentials."""
import secrets
from pathlib import Path

def configure():
    path = Path('.env')
    text = path.read_text() if path.exists() else Path('.env.example').read_text()
    if 'LOCAL_BACKEND_TOKEN=replace-with-a-random-local-token' in text:
        text = text.replace('LOCAL_BACKEND_TOKEN=replace-with-a-random-local-token', 'LOCAL_BACKEND_TOKEN='+secrets.token_urlsafe(32))
    path.write_text(text); path.chmod(0o600)
    print('Local .env configured. Set ALLOWED_EXTENSION_ID and copy the local token into extension options; do not share it.')

if __name__ == '__main__': configure()
