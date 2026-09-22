'use strict';
const $ = id => document.getElementById(id);
const state = {signals:[], x:[], metrics:null, generated:null, language:'en', region:'', topic:'', query:'', expanded:false, failed:false};
const originalCopy = new Map([...document.querySelectorAll('[data-i18n]')].map(e => [e.dataset.i18n,e.innerHTML]));
const arabic = {tagline:'إشارات عالمية. أثر محلي.',intelligence:'الإحاطة',regions:'المناطق',topics:'المواضيع',research:'الأبحاث',system:'النظام',tampa:'تامبا',allTampa:'كل أخبار تامبا',aiTech:'الذكاء الاصطناعي والتقنية',infrastructure:'البنية التحتية',business:'الأعمال',eyebrow:'السعودية · تامبا · إحاطة عالمية',headline:'<strong>اعرف ما يهم</strong><br>قبل أن يضيع<br>وسط الضجيج.',description:'إحاطة تجمع إشارات الذكاء الاصطناعي والبنية التحتية والأسواق والفرص، من السعودية إلى فلوريدا والعالم.',attention:'أخبار تستدعي<br>الانتباه اليوم',signals:'إشارة في هذه الإحاطة',clear:'مسح الفلاتر',actNow:'تحرّك الآن',latest:'أحدث الإشارات',viewAll:'عرض الكل ←',floridaFocus:'فلوريدا تحت المجهر',floridaTitle:'التقنية، الناس والفرص.',floridaDescription:'استكشف الإشارات المرتبطة بتامبا وميامي وولاية فلوريدا.',explore:'استكشف الإشارات ←',systemStatus:'حالة النظام',quick:'إجراءات سريعة',searchSignals:'البحث في الإشارات',openAct:'فتح تحرّك الآن',health:'حالة المصادر',switchLanguage:'Switch to English',saudiIntelligence:'الإحاطة السعودية',floridaUS:'فلوريدا / الولايات المتحدة',footer:'غد أكثر وضوحًا. إحاطة بعد إحاطة.'};
const regions = {
 'Saudi Arabia':[/saudi|riyadh|jeddah|السعود|الرياض|جدة/i,'السعودية'],
 'United States':[/united states|\busa\b|\bu\.s\.|american|pentagon|florida|miami|tampa|واشنطن|أمريك|الأمريك|الولايات المتحدة|البنتاغون/i,'الولايات المتحدة'],
 'Miami':[/miami|ميامي/i,'ميامي'], 'Tampa':[/tampa|تامبا/i,'تامبا'],
 'Florida':[/florida|miami|tampa|orlando|فلوريدا|ميامي|تامبا/i,'فلوريدا'], 'Wyoming':[/wyoming|وايومنغ/i,'وايومنغ'],
 'Europe':[/europe|european|britain|germany|france|أوروب|بريطانيا|ألمانيا|فرنسا/i,'أوروبا'],
 'Asia':[/asia|china|chinese|japan|korea|india|آسيا|الصين|اليابان|كوريا|الهند/i,'آسيا'],
 'Middle East':[/middle east|saudi|iran|israel|yemen|qatar|emirates|السعود|إيران|ايران|إسرائيل|اليمن|قطر|الإمارات|الشرق الأوسط/i,'الشرق الأوسط']
};
const topics = {
 'AI & Agents':[/\bai\b|agent|llm|model|ذكاء|وكلاء|نماذج/i,'الذكاء الاصطناعي والوكلاء'],
 'Infrastructure':[/infrastructure|data cent|compute|cloud|بنية تحتية|البنية التحتية|حوسبة|مركز بيانات/i,'البنية التحتية'],
 'Cybersecurity':[/cyber|security|vulnerab|credential|espionage|أمن|ثغرة|تجسس/i,'الأمن السيبراني'],
 'Research':[/arxiv|research paper|research study|scientific paper|بحث علمي|ورقة بحثية|دراسة علمية/i,'الأبحاث'],
 'Physical AI':[/robot|physical ai|autonomous|روبوت|ذاتي/i,'الذكاء الاصطناعي المادي'],
 'Computer Vision':[/computer vision|imagery|image|satellite|رؤية حاسوبية|صور|أقمار/i,'الرؤية الحاسوبية'],
 'Drones':[/drone|uav|مسير|طائرة/i,'الطائرات المسيّرة'],
 'Business':[/business|investment|funding|market|startup|أعمال|استثمار|تمويل|أسواق/i,'الأعمال'],
 'Real Estate':[/real estate|property|housing|عقار|إسكان/i,'العقارات'],
 'Opportunities':[/opportunity|hiring|grant|fellowship|فرص|توظيف|منحة/i,'الفرص']
};
const esc = value => String(value ?? '').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const t = (en,ar) => state.language === 'ar' ? ar : en;
const source = s => ({github:'GitHub',arxiv:'arXiv',hackernews:'HN',twitter:'X','google-news':'News'}[s.source] || s.source || 'X');
const text = s => [s.title,s.content,s.brief_en,s.brief_ar,s.reason,s.topic,s.region,s.source].filter(Boolean).join(' ');
const summary = s => (state.language === 'ar' ? s.brief_ar || s.brief_en : s.brief_en || s.brief_ar) || s.content || s.text || s.reason || '';
const timestamp = s => s.sourcePublishedAt || s.source_published_at || s.published_at || s.created_at || s.createdAt || s.seen_at || s.timestamp;
function time(value){const d=new Date(value);return Number.isNaN(d.getTime())?'—':d.toLocaleTimeString(state.language==='ar'?'ar-SA':'en-GB',{hour:'2-digit',minute:'2-digit'});}
function safeUrl(value){try{const u=new URL(value);return ['http:','https:'].includes(u.protocol)?u.href:'#';}catch{return '#';}}
function matches(s, region=state.region, topic=state.topic){return (!region || regions[region][0].test(text(s))) && (!topic || topics[topic][0].test(text(s))) && (!state.query || text(s).toLowerCase().includes(state.query.toLowerCase()));}
function menu(){
 $('regionOptions').innerHTML=Object.entries(regions).map(([name,v])=>`<button data-region="${esc(name)}" aria-pressed="${state.region===name}">${esc(t(name,v[1]))}</button>`).join('');
 $('topicOptions').innerHTML=Object.entries(topics).map(([name,v])=>`<button data-topic="${esc(name)}" aria-pressed="${state.topic===name}">${esc(t(name,v[1]))}</button>`).join('');
}
function compact(s){return `<a class="compact-story" href="${esc(safeUrl(s.url || s.source_url || s.primary_source_url))}" target="_blank" rel="noopener noreferrer"><h3 dir="auto">${esc(s.title || s.text || t('Source update','تحديث المصدر'))}</h3><p dir="auto">${esc(summary(s))}</p>${['x','twitter'].includes(s.source)?`<div class="story-meta"><span>${esc(s.evidence_status||t('Source report','رواية المصدر'))}</span><time>${time(timestamp(s))}</time></div>`:''}</a>`;}
function empty(){return `<p class="empty">${t('No matching signals in the current briefing.','لا توجد إشارات مطابقة في الإحاطة الحالية.')}</p>`;}
function render(){
 const filtered=state.signals.filter(s=>matches(s));
 const actions=filtered.filter(s=>s.act_now === true);
 const ranked=[...filtered].sort((a,b)=>Number(b.action_score||b.score||0)-Number(a.action_score||a.score||0));
 $('actionCount').textContent=state.signals.filter(s=>s.act_now===true).length;
 $('totalCount').textContent=state.signals.length;
 $('updatedTime').textContent=time(state.generated);
 const date=new Date(state.generated);
 $('updatedDate').textContent=state.generated&&!Number.isNaN(date.getTime())?t('Last updated ','آخر تحديث ')+date.toLocaleDateString(state.language==='ar'?'ar-SA':'en-GB',{day:'numeric',month:'long',year:'numeric'}):t('Update unavailable','التحديث غير متاح');
 const stale=!state.generated || Number.isNaN(date.getTime()) || Date.now()-date.getTime()>24*60*60*1000;
 $('liveBadge').classList.toggle('stale',stale);
 $('liveText').textContent=state.failed?t('Unavailable','غير متاح'):stale?t('Older briefing','إحاطة سابقة'):t('Live','مباشر');
 $('actionStatus').textContent=actions.length+' '+t('items require attention','أخبار تستدعي الانتباه');
 const featured=actions.length?actions:ranked.slice(0,3);
 $('actionList').innerHTML=(!actions.length?`<div class="empty notice">${t('No action required in this briefing.','لا توجد أخبار تستدعي إجراءً في هذه الإحاطة.')}</div><p class="subheading">${t('Top signals to read','أبرز الإشارات للقراءة')}</p>`:'')+featured.map((s,i)=>`<article class="story"><span class="number">${String(i+1).padStart(2,'0')}</span><div class="story-body"><div class="story-meta"><span>${esc(source(s))} / ${esc(s.topic || 'AI')}</span><time>${time(timestamp(s))}</time></div><h3 dir="auto">${esc(s.title)}</h3><p dir="auto">${esc(summary(s))}</p><div class="chips"><span class="chip ${s.act_now?'red':''}">${s.act_now?t('Action required','يتطلب إجراءً'):t('Read','للقراءة')}</span><span class="chip">${t('Evidence','الأدلة')} ${Number(s.evidence_count || 0)}</span><span class="chip teal">${t('Score','الدرجة')} ${Number(s.score||0)}</span><button class="read" data-story="${state.signals.indexOf(s)}">${t('Read briefing →','قراءة الإحاطة ←')}</button></div></div></article>`).join('')+(!featured.length?empty():'');
 const latest=[...filtered].sort((a,b)=>(Date.parse(timestamp(b))||0)-(Date.parse(timestamp(a))||0));
 $('latestList').innerHTML=latest.slice(0,state.expanded?latest.length:10).map(s=>`<a class="signal-row" href="${esc(safeUrl(s.url))}" target="_blank" rel="noopener noreferrer"><span class="dot"></span><time>${time(timestamp(s))}</time><strong>${esc(source(s))}</strong><span class="headline" title="${esc(s.title)}" dir="auto">${esc(s.title)}</span><span aria-hidden="true">↗</span></a>`).join('')||empty();
 $('viewAll').textContent=state.expanded?t('Show less ↑','عرض أقل ↑'):t('View all →','عرض الكل ←');
 $('saudiList').innerHTML=state.signals.filter(s=>matches(s,'Saudi Arabia','')).slice(0,3).map(compact).join('')||empty();
 $('floridaList').innerHTML=state.signals.filter(s=>matches(s,'United States','')).slice(0,3).map(compact).join('')||empty();
 $('researchList').innerHTML=state.signals.filter(s=>matches(s,'','Research')).slice(0,3).map(compact).join('')||empty();
 const x=state.x.filter(s=>matches(s));
 $('xList').innerHTML=x.map(compact).join('')||empty();
 $('xCount').textContent=x.length+' '+t('public-source posts','منشورًا من مصادر عامة');
 $('healthStatus').textContent=!state.metrics?t('Status unavailable','الحالة غير متاحة'):Number(state.metrics.source_failure_rate)>0?t('Some sources need attention','بعض المصادر تحتاج متابعة'):t('No source failures reported','لم تُسجّل أخطاء في المصادر');
 $('filterbar').hidden=!(state.region||state.topic||state.query);
 $('filterLabel').textContent=[state.region?t(state.region,regions[state.region][1]):'',state.topic?t(state.topic,topics[state.topic][1]):'',state.query].filter(Boolean).join(' · ')+` (${filtered.length})`;
}
function language(value){state.language=value;document.documentElement.lang=value;document.body.dir=value==='ar'?'rtl':'ltr';document.querySelectorAll('[data-i18n]').forEach(e=>{e.innerHTML=value==='ar'?(arabic[e.dataset.i18n]||originalCopy.get(e.dataset.i18n)):originalCopy.get(e.dataset.i18n);});document.querySelectorAll('[data-language]').forEach(b=>{b.classList.toggle('active',b.dataset.language===value);b.setAttribute('aria-pressed',String(b.dataset.language===value));});$('search').placeholder=t('Search AIbrief...','ابحث في إحاطة...');menu();render();}
function closeMenus(){document.querySelectorAll('details[open]').forEach(d=>d.open=false);}
document.addEventListener('click',e=>{
 const b=e.target.closest('button');
 if(b?.hasAttribute('data-region')||b?.hasAttribute('data-topic')){if(b.hasAttribute('data-region'))state.region=b.dataset.region;if(b.hasAttribute('data-topic'))state.topic=b.dataset.topic;closeMenus();menu();render();$('latest').scrollIntoView({block:'start'});}
 if(b?.hasAttribute('data-reset')){state.region='';state.topic='';state.query='';$('search').value='';menu();render();}
 if(b?.dataset.language)language(b.dataset.language);
 if(b?.hasAttribute('data-story')){const s=state.signals[Number(b.dataset.story)];$('dialogTitle').textContent=s.title;$('dialogBody').textContent=summary(s);$('dialogMeta').textContent=source(s)+' · '+time(timestamp(s));$('dialogSource').href=safeUrl(s.url);$('dialogSource').textContent=t('Open original source →','فتح المصدر الأصلي ←');$('storyDialog').dir=state.language==='ar'?'rtl':'ltr';$('storyDialog').showModal();}
 if(!e.target.closest('details'))closeMenus();
});
document.querySelectorAll('details').forEach(d=>d.addEventListener('toggle',()=>{if(d.open)document.querySelectorAll('details').forEach(other=>{if(other!==d)other.open=false;});}));
document.addEventListener('keydown',e=>{if(e.key==='Escape')closeMenus();if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()==='k'){e.preventDefault();$('search').focus();}});
$('storyDialog').querySelector('.close').addEventListener('click',()=>$('storyDialog').close());
$('search').addEventListener('input',e=>{state.query=e.target.value;render();});
$('focusSearch').addEventListener('click',()=>{$('search').scrollIntoView({block:'center'});$('search').focus();});
$('toggleLanguage').addEventListener('click',()=>language(state.language==='en'?'ar':'en'));
$('viewAll').addEventListener('click',()=>{state.expanded=!state.expanded;render();});
async function getJson(path){const response=await fetch(path,{cache:'no-store'});if(!response.ok)throw new Error('Feed unavailable');return response.json();}
async function load(){
 const results=await Promise.allSettled([getJson('data/signals.json'),getJson('data/metrics.json'),getJson('data/breaking_status.json')]);
 if(results[0].status==='fulfilled'){const p=results[0].value;state.signals=(Array.isArray(p)?p:p.signals||[]).filter(s=>!s.duplicate_of);state.generated=p.generated_at;}else{state.failed=true;}
 if(results[1].status==='fulfilled')state.metrics=results[1].value;
 const feed=results[2].status==='fulfilled'?results[2].value.feed:[];
 const raw=[...(Array.isArray(feed)?feed:[]),...state.signals.filter(s=>['twitter','x'].includes(s.source))];
 const seen=new Set();state.x=raw.filter(s=>{const key=safeUrl(s.url||s.source_url);if(key==='#'||seen.has(key))return false;seen.add(key);return true;}).sort((a,b)=>(Date.parse(timestamp(b))||0)-(Date.parse(timestamp(a))||0));
 menu();render();
 if(state.failed){$('actionList').innerHTML=`<p class="empty">${t('The briefing could not be loaded. Please refresh to retry.','تعذر تحميل الإحاطة. حدّث الصفحة للمحاولة مجددًا.')}</p>`;}
}
load();
