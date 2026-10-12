"""Conservative routing hints, with visual classification when available."""
import re

TYPES = ('photo', 'flag', 'chart', 'map', 'process', 'diagram')
GUIDANCE = {
 'photo': 'Describe framing, visible colors, shapes, surface textures, patterns, spatial arrangement and background. Write 3–5 concrete visual sentences: first the subject and framing, then color/shape/texture, then surroundings and background. Do not replace appearance with biology, history or uses.',
 'flag': 'Describe the flag shape and the colors of stripes in their visible order (top to bottom or left to right). State orientation and visible emblems. Do not guess a numeric aspect ratio, symbolism, country identity or color meanings; use a named identity only from the associated source label.',
 'chart': 'Identify the chart type, readable title, axes, units and legend. Explain the main trend or comparison and significant highs/lows. Give numbers only when readable and associated with the correct category. If values are unreadable, say so instead of guessing.',
 'map': 'Describe the area depicted, readable place labels, legend, orientation and highlighted locations or regions. Explain their spatial relationships. If a line meaning is unclear, describe its color and path rather than inventing its role. Do not assume north is up or invent boundaries, distances or map keys.',
 'process': 'Explain each readable stage in its shown order and how arrows connect the stages. Distinguish branches and repeated cycles. OCR reading order is not process order. If connections or labels cannot be read, say which are unclear; never reconstruct missing stages from general knowledge.',
 'diagram': 'Explain the visible layout, readable labels, highlighted elements and their relationships. Describe color/shape coding and its meaning only if the legend or source supports it. Explain the information, not just that the image contains text.'
}


def caption_hint(context, mode):
    if mode != 'context_aware': return None
    data = context.model_dump() if hasattr(context, 'model_dump') else dict(context)
    text = (data.get('caption') or '').lower()
    if re.search(r'\bflag\b', text): return 'flag'
    if re.search(r'\b(life.?cycle|flow.?chart|process diagram|water cycle)\b', text): return 'process'
    if re.search(r'\b(map|projection)\b', text): return 'map'
    if re.search(r'\b(bar chart|line chart|pie chart|scatter plot|histogram|graph)\b', text): return 'chart'
    if re.search(r'\b(diagram|conservation status|periodic table|coat of arms)\b', text): return 'diagram'
    return None


def inspect_image(model, image, context, mode, ocr_image=None, requested_type='auto'):
    classifier = getattr(model, 'classify_image', None)
    hint = caption_hint(context, mode)
    if requested_type in TYPES:
        kind, source = requested_type, 'user'
    elif hint:
        kind, source = hint, 'caption'
    else:
        visual_type = classifier(image) if classifier else 'photo'
        kind = visual_type if visual_type in TYPES else 'photo'
        source = 'visual' if classifier else 'fallback'
    ocr = getattr(model, 'ocr', None)
    text = ocr.extract(ocr_image if ocr_image is not None else image) if ocr else {
        'status':'unavailable', 'engine':'unavailable', 'lines':[], 'ms':0}
    return {'image_type':kind, 'type_source':source, 'ocr':text}
