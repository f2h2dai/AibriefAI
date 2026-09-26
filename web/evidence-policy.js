(function(root) {
  'use strict';
  function url(value) {
    try {
      const u = new URL(value);
      if (!['http:', 'https:'].includes(u.protocol) || u.username || u.password) return '';
      u.hash = '';
      if (/^(www\.)?(x\.com|twitter\.com)$/.test(u.hostname)) {
        const match = u.pathname.match(/^\/[^/]+\/status(?:es)?\/(\d+)\/?$/);
        if (match) return 'https://x.com/i/status/' + match[1];
      }
      return u.href.replace(/\/$/, '');
    } catch (_) { return ''; }
  }
  function status(signal) {
    if (signal.evidence_policy_version !== 1 || !Array.isArray(signal.evidence)) return 'unverified';
    const records = signal.evidence.filter(e => e && url(e.original_url) && e.confirmation_state === 'reviewed_support' && e.reviewer && e.independence_group && !e.correction_url);
    const groups = new Set(records.map(e => e.independence_group));
    return groups.size < 2 ? 'unverified' : records.some(e => e.primary === true) ? 'verified' : 'corroborated';
  }
  function saudi(s) {
    return /\b(saudi|ksa|riyadh|jeddah|neom)\b|السعودي|الرياض|جدة|نيوم/i.test(
      ['title','content','text','reason','brief_en','brief_ar','country','region','topic','market'].map(k => s[k] || '').join(' '));
  }
  function normalize(s) {
    const sourceURL = url(s.url || s.source_url || s.primary_source_url);
    let cap = 75;
    try {
      const u = new URL(s.url || s.source_url || s.primary_source_url);
      const host = u.hostname.replace(/^www\./, '');
      if (['x.com','twitter.com'].includes(host)) cap = /^\/grok\//i.test(u.pathname) || s.is_reply || s.in_reply_to_status_id ? 20 : 60;
      else if (/(\.gov|\.gov\.sa|\.edu)$/.test(host) || ['reuters.com','apnews.com','arxiv.org'].includes(host)) cap = 100;
    } catch (_) { /* Missing source stays unverified. */ }
    const base = Number(s.relevance_score ?? s.score ?? 0);
    return {...s, url: sourceURL || '#', primary_source_url: url(s.primary_source_url),
      sourcePublishedAt: s.event_time || s.sourcePublishedAt || s.source_published_at || s.published_at || s.createdAt,
      content: s.content || s.text || s.reason || '', evidence_status: status(s),
      score: Math.min(cap, Math.max(0, Number.isFinite(base) ? base : 0)), saudi_relevant: saudi(s)};
  }
  function combine(...feeds) {
    const seen = new Set(), result = [];
    for (const s of feeds.flat()) {
      if (!s || typeof s !== 'object' || s.duplicate_of) continue;
      const key = url(s.url || s.source_url || s.primary_source_url) || s.id || s.candidate_id;
      if (key && seen.has(key)) continue;
      if (key) seen.add(key);
      result.push(normalize(s));
    }
    return result;
  }
  root.AIbriefEvidence = {url, status, saudi, normalize, combine};
})(typeof window !== 'undefined' ? window : globalThis);
