"""Bounded image retrieval and preprocessing. Redirects are deliberately denied."""
import base64
import hashlib
import io
import warnings
import httpx
from PIL import Image, ImageOps, UnidentifiedImageError
from backend.schemas import validate_image_url
from backend.errors import ProjectError

MAX_BYTES = 8 * 1024 * 1024
Image.MAX_IMAGE_PIXELS = 20_000_000

def fetch_image(url, user_agent):
    validate_image_url(url)
    try:
        with httpx.Client(timeout=10, follow_redirects=False, trust_env=False) as client:
            with client.stream('GET', url, headers={'User-Agent': user_agent}) as response:
                if 300 <= response.status_code < 400:
                    raise ProjectError('IMAGE_FETCH_FAILED', 'Image redirect denied; choose a Wikimedia thumbnail.', 502)
                response.raise_for_status()
                if int(response.headers.get('content-length', 0)) > MAX_BYTES:
                    raise ProjectError('IMAGE_TOO_LARGE', 'Image exceeds 8 MB.', 413)
                data = bytearray()
                for chunk in response.iter_bytes():
                    data.extend(chunk)
                    if len(data) > MAX_BYTES:
                        raise ProjectError('IMAGE_TOO_LARGE', 'Image exceeds 8 MB.', 413)
                return bytes(data)
    except httpx.HTTPError:
        raise ProjectError('IMAGE_FETCH_FAILED', 'Cannot retrieve image from Wikimedia. Try again or choose another image.', 502, True) from None

def decode_base64(value):
    try:
        data = base64.b64decode(value, validate=True)
    except (ValueError, base64.binascii.Error):
        raise ProjectError('INVALID_IMAGE', 'Image payload is not valid base64.', 422) from None
    if len(data) > MAX_BYTES:
        raise ProjectError('IMAGE_TOO_LARGE', 'Image exceeds 8 MB.', 413)
    return data

def prepare_image(data, max_side=768):
    if len(data) > MAX_BYTES:
        raise ProjectError('IMAGE_TOO_LARGE', 'Image exceeds 8 MB.', 413)
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('error', Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(data)) as original:
                if original.format not in ('JPEG', 'PNG', 'WEBP', 'GIF'):
                    raise ProjectError('UNSUPPORTED_IMAGE', 'Use a JPEG, PNG, WebP or rasterized SVG thumbnail.', 415)
                animated = getattr(original, 'n_frames', 1) > 1
                original.seek(0)
                image = ImageOps.exif_transpose(original)
                if image.width * image.height > 20_000_000:
                    raise ProjectError('IMAGE_TOO_LARGE', 'Image exceeds the 20 megapixel decode limit.', 413)
                image.thumbnail((max_side, max_side), Image.Resampling.LANCZOS)
                # Composite transparent diagrams over white, rather than turning them black.
                if image.mode in ('RGBA', 'LA') or 'transparency' in image.info:
                    rgba = image.convert('RGBA')
                    background = Image.new('RGBA', rgba.size, 'white')
                    image = Image.alpha_composite(background, rgba).convert('RGB')
                else:
                    image = image.convert('RGB')
                image.load()
                image.info.clear()
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError, Image.DecompressionBombWarning):
        raise ProjectError('UNSUPPORTED_IMAGE', 'Image could not be safely decoded as a supported raster.', 415) from None
    out = io.BytesIO()
    image.save(out, format='PNG')
    return image, out.getvalue(), hashlib.sha256(out.getvalue()).hexdigest(), animated
