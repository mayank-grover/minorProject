const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const {JSDOM} = require('jsdom');
const fixture = fs.readFileSync('tests/browser_fixtures/article.html', 'utf8');
function setup(handler) {
  const dom = new JSDOM(fixture, {url:'https://en.wikipedia.org/wiki/Fixture', runScripts:'outside-only'});
  const {window} = dom; let listener;
  window.HTMLElement.prototype.scrollIntoView = function() {};
  window.chrome = {runtime: {onMessage:{addListener:fn => {listener=fn;}}, sendMessage:handler || (() => Promise.resolve({error:'Test network failure'}))}};
  window.eval(fs.readFileSync('extension/context_extractor.js','utf8'));
  return {window,dom,loadUI(){window.eval(fs.readFileSync('extension/content.js','utf8'));listener({type:'TOGGLE'});},toggle(){listener({type:'TOGGLE'});}};
}
test('extracts distinct figures, absent vs empty alt, gallery and infobox without caption leakage',()=>{
  const {window,dom}=setup(); const imgs=window.WikiContext.eligible(); assert.equal(imgs.length,4);
  const a=window.WikiContext.extract(imgs[0],0),b=window.WikiContext.extract(imgs[1],1);
  assert.equal(a.context.caption,'First caption');assert.equal(a.context.existing_alt,'');
  assert.equal(a.context.section_heading,null);assert.equal(b.context.existing_alt,null);
  assert.equal(b.context.caption,'Second caption');assert.equal(b.context.section_heading,'Structure');
  assert(!b.context.nearby_text.includes('Unrelated section'));
  assert.equal(window.WikiContext.extract(imgs[2],2).context.caption,'Gallery caption');
  assert.equal(window.WikiContext.extract(imgs[3],3).context.caption,null);dom.window.close();
});
test('UI keeps alt and links, shows accessible error and removes controls', async()=>{
  const {window,dom,loadUI,toggle}=setup(); const original=window.document.querySelector('img').getAttribute('alt');
  loadUI(); const doc=window.document;
  assert.equal(doc.activeElement.id,'wiki-description-title');assert.equal(doc.querySelectorAll('[data-wiki-description-control]').length,4);
  const trigger=doc.querySelector('[data-wiki-description-control] button');trigger.focus();trigger.click();
  await new Promise(r=>setTimeout(r,0));
  assert(doc.querySelector('[role=status]').textContent.includes('Test network failure'));
  assert([...doc.querySelectorAll('button')].some(b=>b.textContent==='Retry'));
  assert.equal(doc.querySelector('img').getAttribute('alt'),original);assert.equal(doc.querySelector('figure a').getAttribute('href'),'/wiki/File:A.jpg');
  toggle();assert.equal(doc.querySelectorAll('[data-wiki-description-control]').length,0);assert(!doc.querySelector('#wiki-description-panel'));dom.window.close();
});
test('uses textContent for results, keeps focus and discards cancelled responses',async()=>{
  let resolve; const response=new Promise(r=>resolve=r); let payload;
  const env=setup(message=>{payload=message.payload;return response});const {window,dom}=env;env.loadUI();const doc=window.document;
  const trigger=doc.querySelector('[data-wiki-description-control] button');trigger.focus();trigger.click();
  [...doc.querySelectorAll('button')].find(b=>b.textContent==='Cancel request').click();
  resolve({result:{request_id:payload.request_id,occurrence_id:payload.occurrence_id,description:'Late result',model_id:'test',inference_ms:1,limitations:[]}});
  await new Promise(r=>setTimeout(r,0));assert(doc.querySelector('[data-wiki-description-control] section').hidden);dom.window.close();
  const success=setup(async message=>({result:{...message.payload,description:'<b>plain text</b>',model_id:'test',inference_ms:1,limitations:[]}}));success.loadUI();
  const d=success.window.document;const btn=d.querySelector('[data-wiki-description-control] button');btn.focus();btn.click();await new Promise(r=>setTimeout(r,0));
  assert.equal(d.activeElement,btn);assert.equal(d.querySelector('.description').textContent,'<b>plain text</b>');assert(!d.querySelector('.description b'));assert(!d.querySelector('[data-wiki-description-control] section').hidden);
  assert(d.querySelector('.description').closest('[data-wiki-description-control]') === btn.parentElement);
  assert(!d.querySelector('#wiki-description-panel .description'));
  const read = [...btn.parentElement.querySelectorAll('button')].find(b=>b.textContent==='Read description');
  read.click();assert.equal(d.activeElement,btn.parentElement.querySelector('h3'));
  d.dispatchEvent(new success.window.KeyboardEvent('keydown',{key:'Escape'}));assert.equal(d.activeElement,btn);
  success.dom.window.close();
});

test('uses only same-row infobox status labels and omits injected result text',()=>{
  const {window,dom}=setup();
  const table=window.document.querySelector('.infobox');
  table.innerHTML='<tbody><tr><th>Conservation status</th></tr><tr><td><a><img src="https://upload.wikimedia.org/wikipedia/status.png" width="250" height="67"></a><span>Least Concern (IUCN 3.1)</span><div data-wiki-description-control>Injected result</div></td></tr><tr><td>Unrelated caption</td></tr></tbody>';
  const data=window.WikiContext.extract(table.querySelector('img'),0);
  assert.equal(data.context.caption,'Conservation status: Least Concern (IUCN 3.1)');
  assert(!data.context.caption.includes('Injected'));dom.window.close();
});

test('keeps independent inline results beside multiple images',async()=>{
  const env=setup(async m=>({result:{...m.payload,description:m.payload.occurrence_id,model_id:'test',inference_ms:1,limitations:[]}}));env.loadUI();
  const d=env.window.document;const wrappers=[...d.querySelectorAll('[data-wiki-description-control]')];
  for(const w of wrappers.slice(0,2)){w.querySelector('button').click();await new Promise(r=>setTimeout(r,0));}
  assert(!wrappers[0].querySelector('section').hidden);assert(!wrappers[1].querySelector('section').hidden);
  assert.notEqual(wrappers[0].querySelector('section').id,wrappers[1].querySelector('section').id);
  assert.notEqual(wrappers[0].querySelector('.description').textContent,wrappers[1].querySelector('.description').textContent);
  env.dom.window.close();
});

function fakeSpeech(window) {
  const calls = {spoken:[], cancel:0, pause:0, resume:0};
  window.SpeechSynthesisUtterance = class {constructor(text){this.text=text;}};
  window.speechSynthesis = {
    getVoices:()=>[
      {name:'Remote natural',lang:'en-US',localService:false},
      {name:'English',lang:'en-US',localService:true,default:true},
      {name:'English Enhanced',lang:'en-GB',localService:true}
    ],
    speak:u=>calls.spoken.push(u), cancel:()=>calls.cancel++,
    paused:false,
    pause:()=>{calls.pause++;window.speechSynthesis.paused=true;},
    resume:()=>{calls.resume++;window.speechSynthesis.paused=false;}
  };
  return calls;
}
const successDescription = async m=>({result:{...m.payload,description:'Golden florets curve around a dark center.',model_id:'test',inference_ms:1,limitations:[]}});
const tick = ()=>new Promise(r=>setTimeout(r,0));
const namedButton = (root,name)=>[...root.querySelectorAll('button')].find(b=>b.textContent===name);

test('read aloud speaks only description with a local English voice and supports pause, resume, stop and completion',async()=>{
  const env=setup(successDescription); const calls=fakeSpeech(env.window);env.loadUI();
  const w=env.window.document.querySelector('[data-wiki-description-control]');w.querySelector('button').click();await tick();
  const read=namedButton(w,'Read aloud');read.focus();read.click();
  assert.equal(calls.spoken[0].text,w.querySelector('.description').textContent);
  assert.equal(calls.spoken[0].voice.name,'English Enhanced');
  assert.equal(calls.spoken[0].rate,0.95);assert.equal(read.textContent,'Stop reading');
  assert.equal(env.window.document.activeElement,read);
  namedButton(w,'Pause reading').click();assert.equal(calls.pause,1);
  namedButton(w,'Resume reading').click();assert.equal(calls.resume,1);
  read.click();assert.equal(calls.cancel,1);assert.equal(read.getAttribute('aria-pressed'),'false');
  assert(namedButton(w,'Pause reading').hidden);
  read.click();calls.spoken[1].onend();assert.equal(read.textContent,'Read aloud');
  env.dom.window.close();
});

test('new reading stops prior image, stale callbacks cannot stop new audio, refresh and disabling stop speech',async()=>{
  const env=setup(successDescription);const calls=fakeSpeech(env.window);env.loadUI();
  const ws=[...env.window.document.querySelectorAll('[data-wiki-description-control]')];
  for(const w of ws.slice(0,2)){w.querySelector('button').click();await tick();}
  namedButton(ws[0],'Read aloud').click();const old=calls.spoken[0];
  namedButton(ws[0],'Pause reading').click();
  namedButton(ws[1],'Read aloud').click();assert.equal(calls.cancel,1);
  assert.equal(calls.resume,1);assert.equal(env.window.speechSynthesis.paused,false);
  assert.equal(namedButton(ws[0],'Read aloud').getAttribute('aria-pressed'),'false');
  old.onend();assert(namedButton(ws[1],'Stop reading'));
  namedButton(ws[1],'Refresh description').click();assert.equal(calls.cancel,2);await tick();
  namedButton(ws[0],'Read aloud').click();env.toggle();assert.equal(calls.cancel,3);
  env.dom.window.close();
});

test('speech failure is accessible and does not hide the description; page exit stops playback',async()=>{
  const env=setup(successDescription);const calls=fakeSpeech(env.window);env.loadUI();
  const w=env.window.document.querySelector('[data-wiki-description-control]');w.querySelector('button').click();await tick();
  namedButton(w,'Read aloud').click();calls.spoken[0].onerror({error:'synthesis-failed'});
  assert(w.querySelector('[role=status]').textContent.includes('Audio playback failed'));
  assert(!w.querySelector('section').hidden);assert(namedButton(w,'Read aloud'));
  namedButton(w,'Read aloud').click();env.window.dispatchEvent(new env.window.Event('pagehide'));
  assert.equal(calls.cancel,1);assert(namedButton(w,'Read aloud'));
  env.dom.window.close();
});

test('country symbols use their own associated article labels without sibling leakage',()=>{
  const {window,dom}=setup();
  window.document.querySelector('.infobox').innerHTML='<tbody><tr><td><div><span><a href="/wiki/File:Flag.svg"><img src="https://upload.wikimedia.org/wikipedia/flag.png" width="120" height="80" alt="ALT-CANARY"></a></span><div><a href="/wiki/Flag_of_Germany" title="Flag of Germany">Flag</a></div></div><div><span><a href="/wiki/File:Arms.svg"><img src="https://upload.wikimedia.org/wikipedia/arms.png" width="90" height="120"></a></span><div><a href="/wiki/Coat_of_arms_of_Germany" title="Coat of arms of Germany">Coat of arms</a></div></div></td></tr></tbody>';
  const imgs=window.document.querySelectorAll('.infobox img');
  assert.equal(window.WikiContext.extract(imgs[0],0).context.caption,'Flag of Germany');
  assert.equal(window.WikiContext.extract(imgs[1],1).context.caption,'Coat of arms of Germany');
  assert.equal(window.WikiContext.extract(imgs[0],0).context.existing_alt,'ALT-CANARY');
  dom.window.close();
});

test('a named monument caption is preserved and a file name alone does not supply identity',()=>{
  const {window,dom}=setup();const figure=window.document.querySelector('figure');
  figure.querySelector('figcaption').textContent='The Brandenburg Gate in Berlin';
  assert.equal(window.WikiContext.extract(figure.querySelector('img'),0).context.caption,'The Brandenburg Gate in Berlin');
  figure.querySelector('figcaption').remove();figure.querySelector('a').href='/wiki/File:Brandenburg_Gate.jpg';
  assert.equal(window.WikiContext.extract(figure.querySelector('img'),0).context.caption,null);
  dom.window.close();
});

test('description style defaults to automatic and sends the selected accessible option',async()=>{
  let sent;
  const env=setup(async m=>{sent=m.payload;return {result:{...m.payload,description:'A process.',model_id:'test',inference_ms:1,limitations:[],image_type:'process'}}});env.loadUI();
  const w=env.window.document.querySelector('[data-wiki-description-control]');const select=w.querySelector('select');
  assert.equal(select.value,'auto');assert.equal(w.querySelector('label').htmlFor,select.id);
  select.value='process';w.querySelector('button').click();await tick();
  assert.equal(sent.image_type,'process');assert(w.querySelector('.metadata').textContent.includes('process description'));
  assert(namedButton(w,'Read aloud'));env.dom.window.close();
});

test('biography context contains explicit aliases, a bounded page overview and distinct image roles',()=>{
  const {window,dom}=setup();const d=window.document;
  d.querySelector('#firstHeading').textContent='Maya Sol';
  d.querySelector('#mw-content-text').innerHTML='<div class="mw-parser-output"><table class="infobox biography vcard"><tr><th class="infobox-above">Maya Sol</th></tr><tr><td class="infobox-image"><img src="https://upload.wikimedia.org/wikipedia/main.jpg" width="250" height="300"><div class="infobox-caption">Solano in 2020</div></td></tr><tr><th>Born</th><td>Maria Elena Solano (1990)</td></tr></table><p><b>Maria Elena Solano</b>, known professionally as <b>Maya Sol</b>, is a singer and performer with a long career.</p><h2>Performances</h2><p>Sol performed at a festival with a band and several guest musicians.</p><figure><img src="https://upload.wikimedia.org/wikipedia/later.jpg" width="250" height="300"><figcaption>Sol performing in 2021</figcaption></figure><h2>Appearance</h2><p>Her distinctive hairstyle is discussed in this section.</p><figure><img src="https://upload.wikimedia.org/wikipedia/detail.jpg" width="250" height="300"><figcaption>Close-up of Solano</figcaption></figure></div>';
  const imgs=window.WikiContext.eligible();const first=window.WikiContext.extract(imgs[0],0).context;
  assert.equal(first.article_kind,'biography');assert.equal(first.subject_name,'Maya Sol');
  assert(first.subject_aliases.includes('Maria Elena Solano'));assert.equal(first.image_role,'lead');assert(first.lead_subject_association);
  assert(first.page_summary.includes('festival'));assert(first.section_outline.includes('Appearance'));assert(first.image_overview.includes('Sol performing in 2021'));
  const later=window.WikiContext.extract(imgs[1],1).context;
  assert.equal(later.image_role,'contextual');assert.equal(later.image_position,1);assert.equal(later.section_heading,'Performances');
  const before=JSON.stringify(first);const injected=d.createElement('div');injected.setAttribute('data-wiki-description-control','');injected.textContent='INJECTED-DESCRIPTION';d.querySelector('.infobox-caption').append(injected);
  assert(!JSON.stringify(window.WikiContext.extract(imgs[0],0).context).includes('INJECTED-DESCRIPTION'));dom.window.close();
});

test('a country vcard is not misclassified as a person and named caption links are retained',()=>{
  const {window,dom}=setup();const d=window.document;d.querySelector('.infobox').classList.add('vcard');
  const figure=d.querySelector('figure');figure.querySelector('figcaption').innerHTML='The <a href="/wiki/Brandenburg_Gate">Brandenburg Gate</a> in Berlin';
  const context=window.WikiContext.extract(figure.querySelector('img'),0).context;
  assert.equal(context.article_kind,'general');assert.equal(context.subject_name,null);assert.equal(context.caption_subject,'The Brandenburg Gate');dom.window.close();
});
