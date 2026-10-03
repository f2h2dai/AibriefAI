const test = require('node:test');
const assert = require('node:assert/strict');
require('../web/evidence-policy.js');
require('../web/assets/command-center.js');
const P = globalThis.AIbriefEvidence, V = globalThis.AIbriefView;

test('Saudi X signals join the briefing with canonical post deduplication', () => {
  const main = [{title:'Saudi AI investment', url:'https://x.com/reporter/status/123?s=20', source:'twitter'}];
  const x = [{title:'Saudi AI investment', source_url:'https://twitter.com/reporter/status/123'},
    {title:'تطور جديد في الرياض', source_url:'https://x.com/arabic/status/456',source:'x'}];
  const combined = P.combine(main,x);
  assert.equal(combined.length,2);
  assert.equal(combined.filter(P.saudi).length,2);
  assert.equal(combined.filter(V.isX).length,2);
});
test('high score and many related URLs never confer verified status or action', () => {
  const item=P.normalize({title:'Confirmed claim', score:100, act_now:true, status:'verified',
    source_url:'https://x.com/grok/status/123', evidence_count:99, event_time:new Date().toISOString()});
  assert.equal(item.score,20);
  assert.equal(item.evidence_status,'unverified');
  assert.equal(V.actionable(item),false);
});
test('reviewed independent evidence and primary source are required for actions', () => {
  const item={action_score:90,event_time:new Date().toISOString(),evidence_policy_version:1,
    evidence:[{original_url:'https://agency.gov.sa/report',confirmation_state:'reviewed_support',reviewer:'editor',independence_group:'agency',primary:true},
      {original_url:'https://reuters.com/report',confirmation_state:'reviewed_support',reviewer:'editor',independence_group:'reuters'}]};
  assert.equal(V.actionable(item),true);
  item.evidence[1].independence_group='agency';
  assert.equal(V.actionable(item),false);
  item.evidence[1].independence_group='reuters';
  item.event_time='2020-01-01T00:00:00Z';
  assert.equal(V.actionable(item),false);
});
test('region, topic and Arabic searches apply to the same merged records', () => {
  const s={reason:'Saudi data center investment in Riyadh',brief_ar:'استثمار سعودي في مركز بيانات'};
  assert.equal(V.matches(s,'Saudi Arabia','Infrastructure','استثمار'),true);
  assert.equal(V.matches(s,'Miami'),false);
  assert.equal(P.saudi({title:'مسائل معقدة في الرياضيات والفيزياء'}),false);
  assert.equal(V.matches({title:'مسائل في الرياضيات'},'Saudi Arabia'),false);
});
