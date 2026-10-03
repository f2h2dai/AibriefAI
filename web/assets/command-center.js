(function(root) {
  'use strict';
  const policy = root.AIbriefEvidence;
  const regions = {
    'Saudi Arabia': [/\b(saudi|ksa|riyadh|jeddah|neom)\b|السعود|الرياض(?![\u0600-\u06ff])|(?<![\u0600-\u06ff])(?:جدة|نيوم)(?![\u0600-\u06ff])/i, 'السعودية'],
    'United States': [/united states|\busa\b|\bu\.s\.|american|pentagon|florida|miami|tampa|واشنطن|أمريك|الولايات المتحدة|البنتاغون/i, 'الولايات المتحدة'],
    Miami: [/miami|ميامي/i, 'ميامي'], Tampa: [/tampa|تامبا/i, 'تامبا'],
    Florida: [/florida|miami|tampa|orlando|فلوريدا|ميامي|تامبا/i, 'فلوريدا'],
    Wyoming: [/wyoming|وايومنغ/i, 'وايومنغ'], Europe: [/europe|britain|germany|france|أوروب|بريطانيا|ألمانيا|فرنسا/i, 'أوروبا'],
    Asia: [/asia|china|chinese|japan|korea|india|آسيا|الصين|اليابان|كوريا|الهند/i, 'آسيا'],
    'Middle East': [/middle east|saudi|iran|israel|qatar|emirates|السعود|إيران|ايران|إسرائيل|قطر|الإمارات|الشرق الأوسط/i, 'الشرق الأوسط']
  };
  const topics = {
    'AI & Agents': [/\bai\b|agent|llm|model|ذكاء|وكلاء|نماذج/i, 'الذكاء الاصطناعي والوكلاء'],
    Infrastructure: [/infrastructure|data cent|compute|cloud|البنية التحتية|حوسبة|مراكز بيانات/i, 'البنية التحتية'],
    Cybersecurity: [/cyber|security|vulnerab|credential|espionage|أمن|ثغرة|تجسس/i, 'الأمن السيبراني'],
    Research: [/arxiv|research paper|scientific paper|research study|بحث علمي|ورقة بحثية/i, 'الأبحاث'],
    'Physical AI': [/robot|physical ai|autonomous|روبوت|ذاتي/i, 'الذكاء الاصطناعي المادي'],
    'Computer Vision': [/computer vision|imagery|image|satellite|رؤية حاسوبية|صور|أقمار/i, 'الرؤية الحاسوبية'],
    Drones: [/drone|uav|مسير|طائرة/i, 'الطائرات المسيّرة'],
    Business: [/business|investment|funding|market|startup|أعمال|استثمار|تمويل|أسواق/i, 'الأعمال'],
    'Real Estate': [/real estate|property|housing|عقار|إسكان/i, 'العقارات'],
    Opportunities: [/opportunity|hiring|grant|fellowship|فرص|توظيف|منحة/i, 'الفرص']
  };
  const corpus = s => ['title','content','text','reason','brief_en','brief_ar','region','country','market','topic','source'].map(k=>s[k]||'').join(' ');
  const isX = s => /^(x|twitter|birdclaw|x\/twitter)$/i.test(s.source||'') || /^https:\/\/(www\.)?(x\.com|twitter\.com)\//i.test(s.source_url||s.url||'');
  const eventTime = s => s.event_time || s.sourcePublishedAt || s.source_published_at || s.published_at || s.createdAt;
  const fresh = (s, now=Date.now()) => {const date=Date.parse(eventTime(s)); return Number.isFinite(date) && date<=now+600000 && now-date<=48*3600000;};
  const reviewedCount = s => new Set((s.evidence||[]).filter(e=>e.confirmation_state==='reviewed_support' && e.reviewer && e.independence_group && !e.correction_url).map(e=>e.independence_group)).size;
  const actionable = s => policy.status(s)==='verified' && fresh(s) && Number(s.action_score||s.score||0)>=70 && !s.duplicate_of && !Number(s.unsupported_claims||0);
  const matches = (s, region='', topic='', query='') => (!region || regions[region][0].test(corpus(s))) && (!topic || topics[topic][0].test(corpus(s))) && (!query || corpus(s).toLowerCase().includes(query.toLowerCase()));
  root.AIbriefView = {corpus, isX, eventTime, fresh, reviewedCount, actionable, matches};
  if (typeof document === 'undefined') return;
  const $ = id => document.getElementById(id);
  const state = {all:[], main:[], x:[], region:'', topic:'', query:'', language:'en', expanded:false, selected:null, generated:null, xGenerated:null, failed:[], rawSource:'all'};
  const esc = v => String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const t = (en,ar) => state.language==='ar'?ar:en;
  const i18n = {
    tagline:'إشارات عالمية. أثر محلي.', intelligence:'الإحاطة', regions:'المناطق', topics:'المواضيع', research:'الأبحاث', system:'النظام',
    eyebrow:'السعودية · ميامي · إحاطة عالمية', headline:'<strong>اعرف ما يهم</strong><br>قبل أن يضيع<br>وسط الضجيج.',
    description:'إحاطة تجمع إشارات الذكاء الاصطناعي والبنية التحتية والأسواق والفرص، من السعودية إلى ميامي والعالم.',
    attention:'إشارات تستدعي<br>الانتباه', signals:'إشارة فريدة<br>في هذه النسخة', clear:'مسح الفلاتر', actNow:'تحرّك الآن', latest:'أحدث الإشارات',
    viewAll:'عرض الكل ←', saudi:'الإحاطة السعودية', us:'ميامي / الولايات المتحدة',
    signal:'الإشارة', sources:'المصادر', methodology:'المنهجية', systemStatus:'حالة النظام',about:'حول إحاطة'
  };
  const original = new Map([...document.querySelectorAll('[data-i18n]')].map(e=>[e,e.innerHTML]));
  const source = s => ({github:'GitHub',arxiv:'arXiv',hackernews:'HN',twitter:'X',x:'X',birdclaw:'X','google-news':'News'}[s.source]||s.source||'Source');
  const title = s => s.title || s.text || t('Source update','تحديث المصدر');
  const summary = s => policy.status(s)==='unverified' ? (s.content||s.text||s.reason||s.brief_en||'') : (state.language==='ar'?s.brief_ar||s.brief_en:s.brief_en||s.brief_ar)||s.content||s.reason||'';
  const short = (value,n=200) => String(value||'').length>n?String(value).slice(0,n)+'…':String(value||'');
  const label = status => t(status, {unverified:'غير مؤكد',corroborated:'مدعوم بمصادر مستقلة',verified:'مؤكد'}[status]||status);
  const confidence = s => label(policy.status(s));
  const time = value => {const d=new Date(value);return Number.isNaN(d.getTime())?'—':d.toLocaleTimeString(state.language==='ar'?'ar-SA':'en-GB',{hour:'2-digit',minute:'2-digit',timeZone:'Asia/Riyadh'});};
  const dateLabel = value => {const d=new Date(value);return Number.isNaN(d.getTime())?t('Unavailable','غير متاح'):d.toLocaleDateString(state.language==='ar'?'ar-SA':'en-GB',{day:'numeric',month:'short',year:'numeric',timeZone:'Asia/Riyadh'});};
  const empty = (en='No matching signals in this snapshot.',ar='لا توجد إشارات مطابقة في هذه النسخة.') => `<p class="empty">${t(en,ar)}</p>`;
  const icon = name => `<svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true">${({open:'<path d="M11 3h6v6m0-6-9 9M8 4H4v12h12v-4"/>',share:'<circle cx="5" cy="10" r="2"/><circle cx="15" cy="4" r="2"/><circle cx="15" cy="16" r="2"/><path d="m7 9 6-4M7 11l6 4"/>',save:'<path d="M5 3h10v14l-5-3-5 3z"/>'})[name]}</svg>`;
  function menu() {
    $('regionOptions').innerHTML=Object.entries(regions).map(([name,v])=>`<button type="button" data-region="${esc(name)}" aria-pressed="${state.region===name}">${esc(t(name,v[1]))}<svg viewBox="0 0 16 16" aria-hidden="true"><path d="m6 4 4 4-4 4" fill="none" stroke="currentColor"/></svg></button>`).join('');
    const options=Object.entries(topics).map(([name,v])=>`<button type="button" data-topic="${esc(name)}" aria-pressed="${state.topic===name}">${esc(t(name,v[1]))}</button>`).join('');
    $('topicOptions').innerHTML=options; $('regionTopics').innerHTML=options;
  }
  function compact(s) {
    return `<button class="compact-story" type="button" data-story="${state.all.indexOf(s)}"><h3 dir="auto">${esc(short(title(s),150))}</h3><p dir="auto">${esc(short(summary(s),220))}</p><small><span>${esc(source(s))} · ${esc(confidence(s))}</span><time>${esc(time(eventTime(s)))}</time></small></button>`;
  }
  function render() {
    const filtered=state.all.filter(s=>matches(s,state.region,state.topic,state.query) && (state.rawSource!=='x'||isX(s)));
    const actions=filtered.filter(actionable).sort((a,b)=>Number(b.action_score||b.score)-Number(a.action_score||a.score));
    const ranked=[...filtered].sort((a,b)=>Number(b.score||0)-Number(a.score||0));
    $('actionCount').textContent=state.all.filter(actionable).length;
    $('updatedTime').textContent=time(state.generated);
    $('updatedDate').textContent=t('Last briefing · ','آخر إحاطة · ')+dateLabel(state.generated)+' AST';
    $('actionStatus').textContent=actions.length+' '+t('items require attention','إشارات تستدعي الانتباه');
    const featured=actions.length?actions.slice(0,3):ranked.slice(0,3);
    $('actionList').innerHTML=(!actions.length?empty('No verified, fresh signal currently requires action. Top signals for review:','لا توجد إشارة مؤكدة وحديثة تستدعي إجراءً الآن. أبرز الإشارات للمراجعة:'):'')+featured.map((s,i)=>`<article class="story"><span class="number">${String(i+1).padStart(2,'0')}</span><div class="story-body"><div class="story-meta"><span>${esc(source(s))} / ${esc(s.topic||'AI')}</span><time>${time(eventTime(s))}</time></div><h3 dir="auto">${esc(short(title(s),145))}</h3><p dir="auto">${esc(short(summary(s),190))}</p><div class="chips"><span class="chip ${actionable(s)?'red':''}">${t(actionable(s)?'Action required':'Review',actionable(s)?'يتطلب إجراءً':'للمراجعة')}</span><span class="chip">${t('Reviewed evidence','أدلة مراجعة')} ${reviewedCount(s)}</span><span class="chip teal">${esc(confidence(s))}</span><button type="button" class="read" data-story="${state.all.indexOf(s)}">${t('Read briefing →','قراءة الإحاطة ←')}</button></div></div></article>`).join('');
    const latest=[...filtered].sort((a,b)=>(Date.parse(eventTime(b))||0)-(Date.parse(eventTime(a))||0));
    const limit=state.expanded?latest.length:10;
    $('latestList').innerHTML=latest.slice(0,limit).map(s=>`<button class="signal-row" type="button" data-story="${state.all.indexOf(s)}"><i class="dot"></i><time>${time(eventTime(s))}</time><strong>${esc(source(s))}</strong><span class="headline" dir="auto" title="${esc(title(s))}">${esc(title(s))}</span></button>`).join('')||empty();
    $('latestCount').textContent=t(`Showing ${Math.min(limit,latest.length)} of ${latest.length} matching signals · ${state.all.length} unique total`,`عرض ${Math.min(limit,latest.length)} من ${latest.length} إشارة مطابقة · الإجمالي الفريد ${state.all.length}`);
    $('viewAll').textContent=state.expanded?t('Show less ↑','عرض أقل ↑'):t('View all →','عرض الكل ←');
    $('saudiList').innerHTML=filtered.filter(policy.saudi).slice(0,1).map(compact).join('')||empty('No Saudi signals match the current filters.','لا توجد إشارات سعودية مطابقة للفلاتر الحالية.');
    $('usList').innerHTML=ranked.filter(s=>matches(s,'United States')).slice(0,1).map(compact).join('')||empty();
    $('researchList').innerHTML=filtered.filter(s=>matches(s,'','Research')).slice(0,2).map(compact).join('')||empty();
    $('filterbar').hidden=!(state.region||state.topic||state.query||state.rawSource==='x');
    $('filterLabel').textContent=[state.region?t(state.region,regions[state.region][1]):'',state.topic?t(state.topic,topics[state.topic][1]):'',state.query,state.rawSource==='x'?'X':''].filter(Boolean).join(' · ')+` (${filtered.length})`;
    const old=!state.generated||Date.now()-Date.parse(state.generated)>48*3600000;
    $('snapshotStatus').textContent=state.failed.length?t('Some feeds unavailable','بعض المصادر غير متاحة'):old?t('Older snapshot · '+dateLabel(state.generated),'نسخة قديمة · '+dateLabel(state.generated)):t('Briefing updated · '+dateLabel(state.generated),'آخر تحديث للإحاطة · '+dateLabel(state.generated));
    if(state.selected!==null)renderDetails(state.all[state.selected]);
  }
  function detailMarkup(s,mobile=false) {
    const records=Array.isArray(s.evidence)?s.evidence:[];
    const refs=records.length?records: [{original_url:s.source_url||s.url,confirmation_state:'unverified'}];
    const links=refs.filter(e=>policy.url(e.original_url)).map(e=>`<a href="${esc(policy.url(e.original_url))}" target="_blank" rel="noopener noreferrer">${esc(new URL(policy.url(e.original_url)).hostname)} ${icon('open')}<small>${e.confirmation_state==='reviewed_support'?t('Reviewed support','دعم مراجَع'):t('Source link · not independently confirmed','رابط مصدر · غير مؤكد بصورة مستقلة')}</small></a>`).join('');
    return `<span class="chip ${actionable(s)?'red':'teal'}">${esc(confidence(s))}</span><h2 ${mobile?'id="mobileDetailTitle"':''} dir="auto">${esc(title(s))}</h2><div class="detail-meta">${time(eventTime(s))} · ${dateLabel(eventTime(s))}<br>${esc(source(s))} / ${esc(s.topic||'AI')}<br>${fresh(s)?t('Within 48 hours','خلال ٤٨ ساعة'):t('Older or unknown event date','تاريخ الحدث قديم أو غير معروف')}</div><div class="detail-block"><h3>${t('Event / source report','الحدث / رواية المصدر')}</h3><p dir="auto">${esc(summary(s))}</p></div><div class="detail-block"><h3>${t('Why it matters','الأثر')}</h3><p dir="auto">${esc(s.impact||s.why_it_matters||t('Impact has not been assessed independently.','لم يُقيّم الأثر بصورة مستقلة.'))}</p></div><div class="detail-block"><h3>${t('Action','الإجراء')}</h3><p dir="auto">${esc(s.recommended_action||s.action||t(actionable(s)?'Review the evidence and assess applicability.':'Monitor the original source; seek independent confirmation before acting.',actionable(s)?'راجع الأدلة وقيّم مدى انطباقها.':'تابع المصدر الأصلي واطلب تأكيدًا مستقلًا قبل اتخاذ إجراء.'))}</p></div><div class="detail-block"><h3>${t('Evidence','الأدلة')} <span class="chip">${reviewedCount(s)} ${t('reviewed sources','مصادر مراجعة')}</span></h3><div class="evidence-list">${links||empty('No original source available.','المصدر الأصلي غير متاح.')}</div></div><div class="detail-block chips"><span class="chip teal">${esc(confidence(s))}</span><span class="chip">${t('Relevance score','درجة الأهمية')} ${Number(s.score||0)}</span></div><div class="detail-actions"><a class="primary" href="${esc(policy.url(s.source_url||s.url)||'#')}" target="_blank" rel="noopener noreferrer">${t('Open source','فتح المصدر')} ${icon('open')}</a><button type="button" data-share>${icon('share')} ${t('Share','مشاركة')}</button><button type="button" data-save>${icon('save')} ${t('Save','حفظ')}</button></div><p class="status-message" role="status"></p>`;
  }
  function renderDetails(s) {if(!s)return;$('detailContent').innerHTML=detailMarkup(s);if($('detailDialog').open)$('mobileDetailContent').innerHTML=detailMarkup(s,true);}
  function select(index) {
    if(!state.all[index])return;state.selected=index;renderDetails(state.all[index]);
    if(matchMedia('(max-width:1100px)').matches){$('mobileDetailContent').innerHTML=detailMarkup(state.all[index],true);if(!$('detailDialog').open)$('detailDialog').showModal();}
    else {$('workspace').classList.remove('inspector-closed');}
  }
  function language(value) {
    state.language=value;document.documentElement.lang=value;document.body.dir=value==='ar'?'rtl':'ltr';
    original.forEach((copy,e)=>e.innerHTML=value==='ar'?(i18n[e.dataset.i18n]||copy):copy);
    document.querySelectorAll('[data-language]').forEach(b=>{b.classList.toggle('active',b.dataset.language===value);b.setAttribute('aria-pressed',String(b.dataset.language===value));});
    $('search').placeholder=t('Search AIbrief...','ابحث في إحاطة...');$('search').setAttribute('aria-label',t('Search intelligence','ابحث في الإحاطة'));
    menu();render();
  }
  function closeMenus(){document.querySelectorAll('details[open]').forEach(d=>d.open=false);}
  document.addEventListener('click',async e=>{
    const b=e.target.closest('button');
    if(b?.dataset.region||b?.dataset.topic){if(b.dataset.region)state.region=b.dataset.region;if(b.dataset.topic)state.topic=b.dataset.topic;closeMenus();menu();render();$('latest').scrollIntoView({block:'start'});}
    if(b?.hasAttribute('data-reset')){state.region='';state.topic='';state.query='';state.rawSource='all';$('search').value='';menu();render();}
    if(e.target.closest('[data-x-filter]')){state.rawSource='x';state.expanded=true;render();}
    if(b?.hasAttribute('data-methodology')||b?.hasAttribute('data-about')){const method=b.hasAttribute('data-methodology');$('mobileDetailContent').innerHTML=`<h2 id="mobileDetailTitle">${method?t('Methodology','المنهجية'):t('About AIbrief','حول إحاطة')}</h2><p>${method?t('Single-source claims remain unverified. Corroborated claims require reviewed independent sources. Verified claims also require a primary source. Relevance scores do not measure truth. Counts represent unique records in the current snapshot.','الادعاءات أحادية المصدر تبقى غير مؤكدة. الدعم يحتاج مصادر مستقلة مراجعة، والتأكيد يحتاج أيضًا مصدرًا أوليًا. درجة الأهمية لا تقيس صحة الادعاء. الأعداد تمثل السجلات الفريدة في النسخة الحالية.'):t('AIbrief brings together public-source intelligence from Saudi Arabia, the United States and the world. Open any signal to inspect its original source and evidence.','تجمع إحاطة إشارات المصادر العامة من السعودية والولايات المتحدة والعالم. افتح أي إشارة لمراجعة المصدر الأصلي والأدلة.')}</p>`;if(!$('detailDialog').open)$('detailDialog').showModal();}
    if(b?.dataset.language)language(b.dataset.language);
    if(b?.hasAttribute('data-story'))select(Number(b.dataset.story));
    if(b?.hasAttribute('data-save')){try{const saved=JSON.parse(localStorage.getItem('aibrief-saved')||'[]');const s=state.all[state.selected];const url=policy.url(s.source_url||s.url);if(!saved.some(x=>x.url===url))saved.push({url,title:title(s)});localStorage.setItem('aibrief-saved',JSON.stringify(saved));b.closest('.detail-actions').nextElementSibling.textContent=t('Saved on this device.','حُفظ على هذا الجهاز.');}catch{b.closest('.detail-actions').nextElementSibling.textContent=t('Device storage unavailable.','تخزين الجهاز غير متاح.');}}
    if(b?.hasAttribute('data-share')){const s=state.all[state.selected],url=policy.url(s.source_url||s.url);try{await navigator.clipboard.writeText(url);b.closest('.detail-actions').nextElementSibling.textContent=t('Source link copied.','تم نسخ رابط المصدر.');}catch{b.closest('.detail-actions').nextElementSibling.textContent=t('Use Open source to share the original link.','استخدم فتح المصدر لمشاركة الرابط الأصلي.');}}
    if(!e.target.closest('details'))closeMenus();
  });
  document.querySelectorAll('details').forEach(d=>d.addEventListener('toggle',()=>{if(d.open)document.querySelectorAll('details').forEach(other=>{if(other!==d)other.open=false;});}));
  document.addEventListener('keydown',e=>{if(e.key==='Escape')closeMenus();if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()==='k'){e.preventDefault();$('search').focus();}});
  $('search').addEventListener('input',e=>{state.query=e.target.value;render();});
  $('viewAll').addEventListener('click',()=>{state.expanded=!state.expanded;render();});
  $('closeInspector').addEventListener('click',()=>$('workspace').classList.add('inspector-closed'));
  $('detailDialog').querySelector('.close-dialog').addEventListener('click',()=>$('detailDialog').close());
  async function json(path){const r=await fetch(path+'?v='+Date.now(),{cache:'no-store'});if(!r.ok)throw new Error('Feed unavailable');return r.json();}
  async function load(){
    const results=await Promise.allSettled([json('data/signals.json'),json('data/breaking_status.json')]);
    if(results[0].status==='fulfilled'){const p=results[0].value;state.main=Array.isArray(p)?p:p.signals||[];state.generated=p.generated_at;}else state.failed.push('briefing');
    if(results[1].status==='fulfilled'){const p=results[1].value;state.x=Array.isArray(p.feed)?p.feed:[];state.xGenerated=p.updated_at;}else state.failed.push('X');
    state.all=policy.combine(state.main,state.x);menu();render();
    if(state.all.length){state.selected=state.all.indexOf([...state.all].sort((a,b)=>Number(b.score||0)-Number(a.score||0))[0]);renderDetails(state.all[state.selected]);}
    if(!state.all.length && state.failed.length)$('actionList').innerHTML=empty('Feeds could not be loaded. Refresh to retry.','تعذر تحميل المصادر. حدّث الصفحة لإعادة المحاولة.');
  }
  load();
})(typeof window!=='undefined'?window:globalThis);
