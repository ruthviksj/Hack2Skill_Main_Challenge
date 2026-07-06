// ============================================================
// Aftermath AI — Safety Gate (Rule-Based for MVP)
// ============================================================

import type { SafetyStatus } from '../types';

/** Keywords that signal potential safety concern */
const SAFETY_KEYWORDS: { keyword: string; level: SafetyStatus }[] = [
  // Crisis-level keywords
  { keyword: 'kill myself', level: 'crisis' },
  { keyword: 'end it all', level: 'crisis' },
  { keyword: 'suicide', level: 'crisis' },
  { keyword: 'self-harm', level: 'crisis' },
  { keyword: 'not worth living', level: 'crisis' },
  { keyword: 'want to die', level: 'crisis' },
  { keyword: 'no point anymore', level: 'crisis' },
  { keyword: 'better off without me', level: 'crisis' },
  // Urgent-level keywords
  { keyword: 'can\'t go on', level: 'urgent' },
  { keyword: 'give up', level: 'urgent' },
  { keyword: 'everything is ruined', level: 'urgent' },
  { keyword: 'useless now', level: 'urgent' },
  { keyword: 'no future', level: 'urgent' },
  { keyword: 'can\'t face', level: 'urgent' },
  { keyword: 'ashamed', level: 'urgent' },
  { keyword: 'can\'t take it', level: 'urgent' },
  // Concern-level keywords
  { keyword: 'not eating', level: 'concern' },
  { keyword: 'not sleeping', level: 'concern' },
  { keyword: 'stopped talking', level: 'concern' },
  { keyword: 'disappeared', level: 'concern' },
  { keyword: 'locked in room', level: 'concern' },
  { keyword: 'won\'t respond', level: 'concern' },
  { keyword: 'crying', level: 'concern' },
  { keyword: 'panic', level: 'concern' },
];

const SEVERITY_LEVELS: Record<SafetyStatus, number> = {
  safe: 0,
  monitoring: 1,
  concern: 2,
  urgent: 3,
  crisis: 4,
};

export interface SafetyGateResult {
  status: SafetyStatus;
  triggered_keywords: string[];
  should_block_academic_response: boolean;
  should_create_escalation: boolean;
  recommended_action: string;
}

/**
 * Simple rule-based Safety Gate for MVP.
 * Scans content for keywords and buddy-reported urgency.
 */
export function evaluateSafety(
  content: string,
  buddyReportedUrgency?: 'low' | 'medium' | 'high' | 'critical',
  buddyReportedSafety?: SafetyStatus,
): SafetyGateResult {
  const lowerContent = content.toLowerCase();
  const triggered: string[] = [];
  let maxLevel: SafetyStatus = 'safe';

  // Scan for keyword matches
  for (const entry of SAFETY_KEYWORDS) {
    if (lowerContent.includes(entry.keyword)) {
      triggered.push(entry.keyword);
      if (SEVERITY_LEVELS[entry.level] > SEVERITY_LEVELS[maxLevel]) {
        maxLevel = entry.level;
      }
    }
  }

  // Factor in buddy-reported urgency
  if (buddyReportedUrgency === 'critical' || buddyReportedSafety === 'crisis') {
    if (SEVERITY_LEVELS['crisis'] > SEVERITY_LEVELS[maxLevel]) {
      maxLevel = 'crisis';
      triggered.push('buddy_reported_crisis');
    }
  } else if (buddyReportedUrgency === 'high' || buddyReportedSafety === 'urgent') {
    if (SEVERITY_LEVELS['urgent'] > SEVERITY_LEVELS[maxLevel]) {
      maxLevel = 'urgent';
      triggered.push('buddy_reported_urgent');
    }
  } else if (buddyReportedUrgency === 'medium') {
    if (SEVERITY_LEVELS['concern'] > SEVERITY_LEVELS[maxLevel]) {
      maxLevel = 'concern';
      triggered.push('buddy_reported_concern');
    }
  }

  const shouldBlock = SEVERITY_LEVELS[maxLevel] >= SEVERITY_LEVELS['urgent'];
  const shouldEscalate = SEVERITY_LEVELS[maxLevel] >= SEVERITY_LEVELS['concern'];

  let recommendedAction = 'continue_normal';
  if (maxLevel === 'crisis') {
    recommendedAction = 'immediate_human_handoff';
  } else if (maxLevel === 'urgent') {
    recommendedAction = 'suggest_human_contact';
  } else if (maxLevel === 'concern') {
    recommendedAction = 'gentle_safety_check';
  } else if (maxLevel === 'monitoring') {
    recommendedAction = 'monitor_and_continue';
  }

  return {
    status: maxLevel,
    triggered_keywords: triggered,
    should_block_academic_response: shouldBlock,
    should_create_escalation: shouldEscalate,
    recommended_action: recommendedAction,
  };
}
