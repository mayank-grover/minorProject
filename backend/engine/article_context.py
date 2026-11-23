"""Choose editorial emphasis and resolve only explicitly source-associated names."""
import re
import hashlib
import json


def data_of(context):
    return context.model_dump() if hasattr(context, 'model_dump') else dict(context)


def hash_context(context, mode, image_type='auto', language='en'):
    """Stable fingerprint for the context actually used to generate a description."""
    editorial = editorial_context(context, mode, image_type)
    data = data_of(context)
    used = editorial['source']
    if mode == 'context_aware' and (data.get('caption') or '').lower().startswith('conservation status:'):
        used = {'caption': data['caption']}
    if language != 'en':
        used = {**used, '_output_language': language}
    encoded = json.dumps(used, sort_keys=True)
    return hashlib.sha256(encoded.encode('utf-8')).hexdigest()


def resolve_subject(context):
    data = data_of(context)
    caption = (data.get('caption') or '').strip()
    name = data.get('subject_name')
    aliases = [name] + (data.get('subject_aliases') or []) if name else []
    if data.get('article_kind') == 'biography' and name:
        for alias in filter(None, aliases):
            if re.search(r'(?<!\w)' + re.escape(alias) + r'(?!\w)', caption, re.I):
                return name
            # A caption beginning with a source-attested surname is common in
            # biographies. Do not match a different person's full name ending
            # in the same surname (e.g. "Another Smith").
            words = re.findall(r"[\w'-]+", alias)
            words = [w for w in words if w.lower().rstrip('.') not in ('jr','sr','ii','iii','iv')]
            surname = re.escape(words[-1]) if len(words) >= 2 else None
            # "Mandela casting his vote", "Kahlo with her parrots", "Kahlo in 1932".
            if surname and re.match(surname + r'(?:\s+(?:in|at|on|with|during|pictured|\w+ing)\b|$)', caption, re.I):
                return name
            # "Painting of Lovelace seated…", "Daguerreotype of Lovelace" — but not "Lovelace's notes".
            if surname and re.search(r'\b(?:portrait|painting|photograph|photo|daguerreotype|drawing|sketch|bust|statue|engraving)\s+of\s+'
                                     + surname + r"(?!['’]s)(?!\w)", caption, re.I):
                return name
        if data.get('image_role') == 'lead' and data.get('lead_subject_association') and not caption:
            return name
    if data.get('caption_subject'):
        return data['caption_subject']
    if re.match(r'^(?:Flag|Coat of arms) of [A-Z]', caption) and len(caption) <= 100:
        return caption
    # Compatibility for older extension snapshots: only short source phrases,
    # not article titles, alt text, filenames or arbitrary long captions.
    if len(caption) <= 100 and re.match(r'^(?:The\s+)?[A-Z][\w-]*(?:\s+[A-Z][\w-]*)+\s+(?:in|of)\s+[A-Z]', caption):
        return re.split(r'\s+in\s+\d{4}\b', caption)[0]
    return None


def editorial_context(context, mode, image_type):
    if mode != 'context_aware': return {'focus':'visual', 'subject':None, 'source':{}}
    data = data_of(context)
    # Routing fields (article_kind, image_role, image_position, lead_subject_association) steer
    # the code below, not the model: shown to it, they were echoed ("a 'general' article").
    # image_overview (other images' captions) is also withheld: the model attributed them to this
    # image (dev: a tectonic-plate map "includes a paleomap drawn by Wegener").
    # subject_name/aliases are article-level: they resolve the subject below; only a resolved,
    # caption-associated subject reaches the prompt.
    source = {k:data.get(k) for k in ('article_title','page_summary','section_outline',
              'caption','caption_subject','section_heading') if data.get(k) is not None}
    # Selected-section context is more useful for later images than the lead.
    if data.get('image_role') != 'lead' and data.get('nearby_text'):
        source['nearby_text'] = data['nearby_text'][:800]
    role = data.get('image_role')
    detail = ' '.join(filter(None, (data.get('caption'),data.get('section_heading')))).lower()
    if image_type == 'photo' and re.search(r'\b(close.?up|portrait|face|facial|tattoos?|hairstyle|appearance)\b', detail):
        focus = 'appearance'
    elif image_type == 'photo' and role == 'lead' and data.get('article_kind') == 'biography':
        focus = 'appearance'
    elif image_type == 'photo' and role == 'contextual':
        focus = 'activity'
    else:
        focus = 'visual'
    return {'focus':focus, 'subject':resolve_subject(context), 'source':source}


def integrate_subject(raw, subject):
    if not subject: return raw
    if re.match(r'^(?:Flag|Coat of arms) of ', subject):
        subject = 'The ' + subject[0].lower() + subject[1:]
    if raw.casefold().startswith(subject.casefold()): return raw
    first_sentence = re.split(r'(?<=[.!?])\s', raw, maxsplit=1)[0]
    if re.search(r'(?<!\w)' + re.escape(re.sub(r'^The ', '', subject)) + r'(?!\w)', first_sentence, re.I):
        return raw
    # Replace a generic opening noun, retaining the model's visual details.
    opening = r'^(?P<preamble>The image (?:shows|depicts)\s+)?(?:A|An|The)\s+(?:(?:large|small|young|older|elderly|golden|black|white|rectangular)\s+){0,3}(?:man|woman|person|performer|singer|rapper|flag|gate|bridge|building|monument)\b'
    if re.match(opening, raw, re.I):
        return re.sub(opening, lambda match:(match.group('preamble') or '') + subject, raw, count=1, flags=re.I)
    # A grammatical introduction identifies the subject without reciting the caption.
    introductory = subject[0].lower() + subject[1:] if subject.startswith('The ') else subject
    return 'The image shows ' + introductory + '. ' + raw
