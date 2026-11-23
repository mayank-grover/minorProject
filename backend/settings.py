import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass
class Settings:
    description_provider: str = os.getenv('DESCRIPTION_PROVIDER', 'local').strip().lower()
    token: str = os.getenv('LOCAL_BACKEND_TOKEN', '')
    extension_id: str = os.getenv('ALLOWED_EXTENSION_ID', '')
    device: str = os.getenv('MODEL_DEVICE', 'auto')
    model_id: str = os.getenv('MODEL_ID', 'HuggingFaceTB/SmolVLM2-2.2B-Instruct')
    revision: str = os.getenv('MODEL_REVISION', '482adb537c021c86670beed01cd58990d01e72e4')
    user_agent: str = os.getenv('WIKIMEDIA_USER_AGENT', 'WikiImageAccessibility/0.1 (local student prototype)')
    timeout: float = float(os.getenv('REQUEST_TIMEOUT_SECONDS', '120'))
    load_model: bool = os.getenv('LOAD_MODEL', '1') == '1'
    max_tokens: int = int(os.getenv('MAX_NEW_TOKENS', '192'))
    groq_api_key: str = os.getenv('GROQ_API_KEY', '')
    groq_model: str = os.getenv('GROQ_MODEL', 'qwen/qwen3.8-27b')
    cache_path: str = os.getenv('DESCRIPTION_CACHE_PATH', 'artifacts/cache.sqlite3')
    neural_tts_enabled: bool = os.getenv('NEURAL_TTS_ENABLED', '1') == '1'
    neural_tts_warmup: bool = os.getenv('NEURAL_TTS_WARMUP', '1') == '1'
