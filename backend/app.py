import asyncio
import hashlib
import hmac
import json
import logging
import threading
import time
from contextlib import asynccontextmanager
from concurrent.futures import ThreadPoolExecutor
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from backend.schemas import DescribeRequest, DescribeResponse
from backend.settings import Settings
from backend.models.smolvlm import SmolVLM
from backend.data.images import fetch_image, decode_base64, prepare_image
from backend.engine.generate import run_generation
from backend.errors import ProjectError

log = logging.getLogger('wiki_describe')

def create_app(settings=None, model=None):
    settings = settings or Settings()
    adapter = model or SmolVLM(settings.revision, settings.device, settings.max_tokens)
    lane = threading.Lock()
    executor = ThreadPoolExecutor(max_workers=1)

    @asynccontextmanager
    async def lifespan(app):
        if model is None and settings.load_model:
            try:
                await asyncio.get_running_loop().run_in_executor(executor, adapter.load)
                log.info('Model ready: %s', adapter.model_id)
            except Exception as exc:
                log.error('Model unavailable (%s). See setup instructions.', type(exc).__name__)
        yield
        executor.shutdown(wait=False, cancel_futures=True)

    app = FastAPI(title='Wikipedia Image Accessibility', version='0.1.0', lifespan=lifespan)
    app.state.model = adapter
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=['127.0.0.1', 'localhost', 'testserver'])
    origins = [f'chrome-extension://{settings.extension_id}'] if settings.extension_id else []
    app.add_middleware(CORSMiddleware, allow_origins=origins, allow_methods=['POST', 'GET'], allow_headers=['Authorization', 'Content-Type'])

    @app.middleware('http')
    async def limits_and_origin(request, call_next):
        origin = request.headers.get('origin')
        if origin and origin not in origins:
            return JSONResponse({'error': {'code': 'ORIGIN_DENIED', 'message': 'Configure this extension ID on the backend.', 'retryable': False}}, status_code=403)
        if request.url.path in ('/describe', '/v1/descriptions'):
            try:
                size = int(request.headers.get('content-length', 0))
            except ValueError:
                size = 12_000_001
            if size > 12_000_000:
                return JSONResponse({'error': {'code': 'REQUEST_TOO_LARGE', 'message': 'Request exceeds 12 MB.', 'retryable': False}}, status_code=413)
            # Bound chunked bodies too, before JSON parsing.
            body = bytearray()
            async for chunk in request.stream():
                body.extend(chunk)
                if len(body) > 12_000_000:
                    return JSONResponse({'error': {'code': 'REQUEST_TOO_LARGE', 'message': 'Request exceeds 12 MB.', 'retryable': False}}, status_code=413)
            request._body = bytes(body)
        return await call_next(request)

    @app.exception_handler(ProjectError)
    async def project_error(request, exc):
        return JSONResponse({'status': 'error', 'error': {'code': exc.code, 'message': exc.message, 'retryable': exc.retryable}}, status_code=exc.status)

    @app.exception_handler(RequestValidationError)
    async def validation_error(request, exc):
        # Do not echo model payloads or Pydantic input fields into logs/responses.
        fields = ['.'.join(str(x) for x in e['loc']) for e in exc.errors()]
        return JSONResponse({'status': 'error', 'error': {'code': 'INVALID_REQUEST', 'message': 'Invalid or missing fields: ' + ', '.join(fields), 'retryable': False}}, status_code=422)

    @app.get('/health')
    async def health():
        config = adapter.configuration()
        return {'status': 'ok' if adapter.ready else 'degraded', 'model_ready': adapter.ready,
                'model_id': adapter.model_id, 'model_revision': adapter.revision,
                'processing': 'local', 'busy': lane.locked(), 'schema_version': '1.0',
                'ocr_engine': getattr(getattr(adapter, 'ocr', None), 'engine', 'unavailable'),
                'authentication_configured': bool(settings.token),
                'extension_configured': bool(settings.extension_id),
                'configuration_fingerprint': hashlib.sha256(json.dumps(config, sort_keys=True).encode()).hexdigest()[:16]}

    def work(payload):
        start = time.perf_counter()
        try:
            data = decode_base64(payload.image_base64) if payload.image_base64 else fetch_image(payload.image_url, settings.user_agent)
            image, _, digest, animated = prepare_image(data)
            ocr_image = prepare_image(data, max_side=1600)[0] if getattr(adapter, 'ocr', None) else image
            result = run_generation(adapter, image, payload.context, payload.mode, payload.detail,
                                    ocr_image=ocr_image, requested_type=payload.image_type)
            limitations = result['limitations']
            if animated:
                limitations.append('Only the first animation frame was described.')
            response = DescribeResponse(request_id=payload.request_id, occurrence_id=payload.occurrence_id,
                description=result['description'], mode=payload.mode, detail=payload.detail,
                model_id=adapter.model_id, model_revision=adapter.revision, prompt_version=result['prompt_version'],
                inference_ms=result['inference_ms'], total_ms=(time.perf_counter()-start)*1000,
                image_hash=digest, context_hash=result['context_hash'], limitations=limitations,
                image_type=result['image_type'], ocr_status=result['ocr_status'], analysis_ms=result['analysis_ms'])
            log.info('request=%s status=ok inference_ms=%.1f', payload.request_id, response.inference_ms)
            return response
        finally:
            # Held until actual compute ends, including after a caller times out/cancels.
            lane.release()

    @app.post('/v1/descriptions', response_model=DescribeResponse)
    @app.post('/describe', response_model=DescribeResponse)
    async def describe(payload: DescribeRequest, request: Request):
        expected = 'Bearer ' + settings.token
        if not settings.token or not hmac.compare_digest(request.headers.get('authorization', ''), expected):
            raise ProjectError('UNAUTHORIZED', 'Configure the local backend token in extension options.', 401)
        if not adapter.ready:
            raise ProjectError('MODEL_UNAVAILABLE', 'Local VLM is not loaded. Check backend setup and /health.', 503, True)
        if not lane.acquire(blocking=False):
            raise ProjectError('BACKEND_BUSY', 'Another image is being described. Wait and retry.', 429, True)
        future = asyncio.get_running_loop().run_in_executor(executor, work, payload)
        try:
            return await asyncio.wait_for(asyncio.shield(future), settings.timeout)
        except asyncio.TimeoutError:
            # Retrieve late exceptions to avoid unhandled-future warnings.
            future.add_done_callback(lambda f: f.exception() if not f.cancelled() else None)
            raise ProjectError('GENERATION_TIMEOUT', 'Generation exceeded the deadline. Wait for the model to finish before retrying.', 504, True) from None

    return app

app = create_app()
