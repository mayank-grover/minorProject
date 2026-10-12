"""Start the local backend: python3 run.py (no environment activation needed)."""
import os
from pathlib import Path
import sys


def main():
    root = Path(__file__).resolve().parent
    python = root / '.venv' / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
    if not python.is_file():
        print('The project Python environment is missing. Follow Installation in README.md first.', file=sys.stderr)
        return 1
    if not (root / '.env').is_file():
        print('Local settings are missing. Follow setup in README.md to create .env and configure the extension.', file=sys.stderr)
        return 1

    os.chdir(root)
    env = os.environ.copy()
    env.setdefault('HF_HOME', str(root / '.cache' / 'huggingface'))
    env.setdefault('PYTORCH_ENABLE_MPS_FALLBACK', '1')
    print('Starting Wikipedia Image Descriptions at http://127.0.0.1:8000', flush=True)
    print('Wait for "Application startup complete", then use the Chrome extension.', flush=True)
    print('Keep this terminal open. Press Control+C to stop.', flush=True)
    # Replace the launcher so Control+C reaches the server directly. The project
    # interpreter works even when python3 is macOS's older system Python.
    os.execve(str(python), [str(python), '-m', 'uvicorn', 'backend.app:app',
                          '--host', '127.0.0.1', '--port', '8000'], env)


if __name__ == '__main__':
    sys.exit(main())
