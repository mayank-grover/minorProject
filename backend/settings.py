import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass
class Settings:
    token: str = os.getenv('LOCAL_BACKEND_TOKEN', '')
    extension_id: str = os.getenv('ALLOWED_EXTENSION_ID', '')
    device: str = os.getenv('MODEL_DEVICE', 'auto')
    revision: str = os.getenv('MODEL_REVISION', 'main')
    user_agent: str = os.getenv('WIKIMEDIA_USER_AGENT', 'WikiImageAccessibility/0.1 (local student prototype)')
    timeout: float = float(os.getenv('REQUEST_TIMEOUT_SECONDS', '120'))
    load_model: bool = os.getenv('LOAD_MODEL', '1') == '1'
    max_tokens: int = int(os.getenv('MAX_NEW_TOKENS', '192'))
