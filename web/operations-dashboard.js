(function(root) {
  'use strict';

  function number(value, fallback) {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : (fallback || 0);
  }

  function actionScore(signal) {
    return number(signal.action_score, number(signal.score, 0));
  }

  function qualifiesForActNow(signal, threshold) {
    return actionScore(signal) >= number(threshold, 70) &&
      number(signal.evidence_count, 0) >= 2 &&
      Boolean(signal.primary_source_url) &&
      number(signal.unsupported_claims, 0) === 0 &&
      (signal.duplicate_of === null || typeof signal.duplicate_of === 'undefined');
  }

  function recalculate(signals, threshold) {
    const minimum = Math.max(0, Math.min(100, number(threshold, 70)));
    const visible = (Array.isArray(signals) ? signals : []).filter(function(signal) {
      return actionScore(signal) >= minimum;
    });
    const actNow = visible.filter(function(signal) {
      return qualifiesForActNow(signal, minimum);
    });
    const distribution = {};
    visible.forEach(function(signal) {
      const source = String(signal.source || 'unknown');
      distribution[source] = (distribution[source] || 0) + 1;
    });
    const cost = visible.reduce(function(total, signal) {
      return total + number(signal.estimated_cost_usd, 0);
    }, 0);
    const failureRate = visible.length ? (visible.length - actNow.length) / visible.length : 0;
    const risk = failureRate <= 0.10 ? 'low' : (failureRate <= 0.30 ? 'moderate' : 'elevated');

    return {
      threshold: minimum,
      visible_signals: visible.length,
      act_now_count: actNow.length,
      estimated_daily_cost: Number(cost.toFixed(6)),
      estimated_false_positive_risk: risk,
      source_distribution: distribution,
      visible: visible,
      act_now: actNow
    };
  }

  root.AIbriefScenario = {
    actionScore: actionScore,
    qualifiesForActNow: qualifiesForActNow,
    recalculate: recalculate
  };
})(typeof window !== 'undefined' ? window : globalThis);
