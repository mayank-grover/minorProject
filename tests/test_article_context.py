import hashlib
import json
import pytest
from PIL import Image
from backend.schemas import Context
from backend.engine.article_context import editorial_context, resolve_subject, integrate_subject
from backend.engine.generate import run_generation
from backend.models.smolvlm import ModelOutput


def biography(**kwargs):
    data={'article_title':'Maya Sol','article_kind':'biography','subject_name':'Maya Sol',
          'subject_aliases':['Maria Elena Solano','Maya Sol'],'page_summary':'Maria Elena Solano is known professionally as Maya Sol.',
          'section_outline':['Early life','Performances','Appearance'], 'image_overview':['Solano in 2020','Sol performing'],'caption':'Solano in 2020',
          'image_role':'lead','image_position':0,'lead_subject_association':True}
    data.update(kwargs)
    return Context(**data)


def test_alias_names_generalize_and_do_not_match_another_person():
    assert resolve_subject(biography())=='Maya Sol'
    assert resolve_subject(biography(caption='Sol performing on stage'))=='Maya Sol'
    assert resolve_subject(biography(caption='Another Solano in 2020',lead_subject_association=False)) is None
    assert resolve_subject(Context(article_title='Maya Sol',caption='An unidentified audience member')) is None


def test_lead_portrait_later_action_and_later_closeup_focus():
    assert editorial_context(biography(),'context_aware','photo')['focus']=='appearance'
    assert editorial_context(biography(image_role='contextual',image_position=3,caption='Sol performing in 2021'),'context_aware','photo')['focus']=='activity'
    assert editorial_context(biography(image_role='contextual',caption='Close-up of Solano face tattoos'),'context_aware','photo')['focus']=='appearance'
    assert editorial_context(biography(),'context_aware','flag')['focus']=='visual'
    assert editorial_context(Context(article_title='A cathedral',image_role='lead'),'context_aware','photo')['focus']=='visual'


def test_title_alone_is_not_identity_but_uncaptioned_primary_infobox_is_associated():
    assert resolve_subject(biography(caption=None))=='Maya Sol'
    assert resolve_subject(biography(caption=None,lead_subject_association=False)) is None
    assert resolve_subject(Context(article_title='Maya Sol')) is None


def test_integrated_subject_retains_visual_action_and_does_not_repeat_caption():
    raw='A man with long hair holds a microphone.'
    assert integrate_subject(raw,'Maya Sol')=='Maya Sol with long hair holds a microphone.'
    assert integrate_subject('The flag has three horizontal stripes.','Flag of Germany')=='The flag of Germany has three horizontal stripes.'
    assert integrate_subject('Maya Sol waves to a crowd.','Maya Sol')=='Maya Sol waves to a crowd.'
    assert integrate_subject('The image shows a man with long hair.','Maya Sol')=='The image shows Maya Sol with long hair.'
    assert integrate_subject('The image shows Maya Sol with long hair.','Maya Sol')=='The image shows Maya Sol with long hair.'


def test_context_focus_and_identity_reach_model_and_hash_but_not_image_only(fake_model):
    context=biography(nearby_text='UNRELATED-SECTION',existing_alt='ALT-CANARY')
    fake_model.generate=lambda *args:ModelOutput('A person holds a microphone.',1,8,'stop')
    result=run_generation(fake_model,Image.new('RGB',(64,64)),context,'context_aware')
    assert result['description'].startswith('Maya Sol holds')
    assert result['resolved_subject']=='Maya Sol' and result['description_focus']=='appearance'
    assert 'hairstyle' in result['prompt'] and 'Do not infer ethnicity' in result['prompt']
    assert 'ALT-CANARY' not in result['prompt'] and 'UNRELATED-SECTION' not in result['prompt']
    used=editorial_context(context,'context_aware','photo')['source']
    assert result['context_hash']==hashlib.sha256(json.dumps(used,sort_keys=True).encode()).hexdigest()
    baseline=run_generation(fake_model,Image.new('RGB',(64,64)),context,'image_only')
    assert baseline['description']==baseline['raw_output']
    assert 'Maya Sol' not in baseline['prompt'] and 'Solano' not in baseline['prompt']


def test_depiction_captions_resolve_but_unrelated_images_in_a_biography_do_not():
    lovelace = lambda caption: biography(article_title='Ada Lovelace', subject_name='Ada Lovelace',
        subject_aliases=['The Countess of Lovelace'], caption=caption, image_role='contextual', lead_subject_association=False)
    assert resolve_subject(lovelace('Painting of Lovelace seated at a piano, by Henry Phillips (1852)'))=='Ada Lovelace'
    assert resolve_subject(lovelace('Daguerreotype of Lovelace (c. 1843)'))=='Ada Lovelace'
    assert resolve_subject(lovelace('Lovelace casting a vote'))=='Ada Lovelace'
    assert resolve_subject(lovelace("Lovelace's notes on the Analytical Engine")) is None
    assert resolve_subject(lovelace('Naturaleza muerta, 1925')) is None


def test_unresolved_subject_is_not_offered_to_the_model(fake_model):
    context = biography(article_title='Frida Kahlo', subject_name='Frida Kahlo', subject_aliases=['Magdalena Carmen Frida Kahlo'],
                        caption='Naturaleza muerta, 1925', image_role='contextual', lead_subject_association=False)
    analysis = {'image_type':'photo','type_source':'visual','ocr':{'status':'no_text','engine':'test','ms':0,'lines':[]}}
    fake_model.generate = lambda *args: ModelOutput('A blue vase holds pink roses.', 1, 8, 'stop')
    result = run_generation(fake_model, Image.new('RGB',(64,64)), context, 'context_aware', analysis=analysis)
    assert result['resolved_subject'] is None and result['description'] == 'A blue vase holds pink roses.'
    prompt = result['prompt'].split('ARTICLE OVERVIEW')[1]
    assert 'does not associate a person with this image' in prompt and 'Magdalena' not in prompt and 'Integrate this name' not in prompt
