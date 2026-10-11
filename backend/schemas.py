from typing import Literal
from urllib.parse import urlsplit
from pydantic import BaseModel, ConfigDict, Field, model_validator, field_validator

class StrictModel(BaseModel):
    model_config = ConfigDict(extra='forbid')


def validate_article_url(value):
    u = urlsplit(value)
    if (u.scheme != 'https' or u.hostname != 'en.wikipedia.org' or u.username or u.password
            or u.port not in (None, 443) or not u.path.startswith('/wiki/')
            or ':' in u.path[len('/wiki/'):]):
        raise ValueError('Only English Wikipedia article read URLs are supported')
    if u.query:
        raise ValueError('Use canonical /wiki/ article URL without query parameters')
    return value


def validate_image_url(value):
    u = urlsplit(value)
    if (u.scheme != 'https' or u.hostname not in ('upload.wikimedia.org', 'thumb.wikimedia.org') or u.username or u.password
            or u.port not in (None, 443) or not u.path.startswith('/wikipedia/') or u.fragment):
        raise ValueError('Only HTTPS Wikimedia upload/thumbnail image references are supported')
    return value

class Context(StrictModel):
    article_title: str = Field(min_length=1, max_length=300)
    caption: str | None = Field(default=None, max_length=1200)
    section_heading: str | None = Field(default=None, max_length=300)
    nearby_text: str | None = Field(default=None, max_length=3200)
    existing_alt: str | None = Field(default=None, max_length=600)

class DescribeRequest(StrictModel):
    schema_version: Literal['1.0'] = '1.0'
    request_id: str = Field(min_length=1, max_length=64)
    occurrence_id: str = Field(min_length=1, max_length=128)
    article_url: str = Field(max_length=2048)
    revision_id: int | None = Field(default=None, gt=0)
    image_url: str = Field(max_length=2048)
    image_base64: str | None = Field(default=None, max_length=11184812)
    context: Context
    mode: Literal['image_only', 'context_aware'] = 'context_aware'
    detail: Literal['concise', 'detailed'] = 'concise'

    _article = field_validator('article_url')(validate_article_url)
    _image = field_validator('image_url')(validate_image_url)

    @model_validator(mode='after')
    def context_budget(self):
        text = ' '.join(x for x in self.context.model_dump().values() if x is not None)
        if len(text) > 8000 or len(text.split()) > 800:
            raise ValueError('Context exceeds 800 words / 8000 characters')
        return self

class DescribeResponse(StrictModel):
    schema_version: Literal['1.0'] = '1.0'
    request_id: str
    occurrence_id: str
    description: str = Field(min_length=1)
    mode: Literal['image_only', 'context_aware']
    detail: Literal['concise', 'detailed']
    model_id: str
    model_revision: str
    prompt_version: str
    inference_ms: float = Field(ge=0)
    total_ms: float = Field(ge=0)
    image_hash: str
    context_hash: str
    generated: Literal[True] = True
    limitations: list[str]
