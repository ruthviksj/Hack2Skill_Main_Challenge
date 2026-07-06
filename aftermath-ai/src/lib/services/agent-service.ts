// ============================================================
// Aftermath AI — Agent Service
// ============================================================
// Orchestrates agent calls, logging, and state management

import { db, generateId, findByUserId, addItem, DEMO_USER_ID } from '../db';
import { RealAgentAdapter } from '../agent/real-adapter';
import type { AgentAdapter, AgentContext } from '../agent/adapter';
import type {
  AgentTurnRequest, AgentTurnResponse, AgentSignalRequest,
  AgentRun, ChatMessage, EscalationEvent, ContinuityPacket,
  SafetyStatus,
} from '../types';
import { evaluateSafety } from '../agent/safety-gate';

// Swapped from MockAgentAdapter to RealAgentAdapter
const adapter: AgentAdapter = new RealAgentAdapter();

function buildContext(userId: string): AgentContext {
  const messages = findByUserId(db.chat_messages, userId).slice(-10);
  const exams = findByUserId(db.exams, userId);
  const packets = findByUserId(db.continuity_packets, userId).filter(p => p.active);
  const missingExam = exams.find(e => e.status === 'outcome_missing');

  return {
    recentMessages: messages.map(m => ({ role: m.role, content: m.content })),
    exams: exams.map(e => ({
      name: e.name,
      status: e.status,
      exam_date: e.exam_date,
      expected_score: e.expected_score,
      actual_score: e.actual_score,
    })),
    continuityRules: packets.flatMap(p => p.future_response_rules_json),
    currentMode: missingExam ? 'aftermath' : 'normal',
    currentPhase: 'phase_0',
    safetyStatus: 'safe',
    hasMissingClosure: !!missingExam,
    missingClosureExam: missingExam?.name,
  };
}

export async function processAgentTurn(request: AgentTurnRequest): Promise<AgentTurnResponse> {
  const context = buildContext(request.user_id);

  // Save user message
  const userMessage: ChatMessage = {
    id: generateId('msg'),
    user_id: request.user_id,
    role: 'user',
    content: request.content,
    mode: context.currentMode,
    phase: context.currentPhase,
    created_at: new Date().toISOString(),
  };
  addItem(db.chat_messages, userMessage);

  // Get agent response
  const response = await adapter.processTurn(request, context);

  // Save assistant message
  const assistantMessage: ChatMessage = {
    id: generateId('msg'),
    user_id: request.user_id,
    role: 'assistant',
    content: response.assistant_response,
    mode: response.mode,
    phase: response.phase,
    suggested_buttons: response.suggested_buttons,
    created_at: new Date().toISOString(),
  };
  addItem(db.chat_messages, assistantMessage);

  // Create signal for the chat
  addItem(db.signals, {
    id: generateId('sig'),
    user_id: request.user_id,
    source_type: 'student',
    signal_type: 'chat',
    raw_content: request.content,
    summary: `Student chat in ${response.mode} mode`,
    sensitivity: response.safety_status === 'safe' ? 'low' : 'high',
    confidence: 0.9,
    metadata_json: { mode: response.mode, phase: response.phase },
    created_at: new Date().toISOString(),
  });

  // Log agent run
  const agentRun: AgentRun = {
    id: generateId('run'),
    user_id: request.user_id,
    input_signal_id: userMessage.id,
    phase: response.phase,
    mode: response.mode,
    safety_status: response.safety_status,
    selected_action: response.selected_action,
    evidence_json: response.evidence,
    response_constraints_json: context.continuityRules,
    memory_updates_json: [],
    created_at: new Date().toISOString(),
  };
  addItem(db.agent_runs, agentRun);

  // Handle escalation if needed
  if (response.escalation_created) {
    createEscalationFromResponse(request.user_id, userMessage.id, response);
  }

  return response;
}

export async function processAgentSignal(request: AgentSignalRequest): Promise<AgentTurnResponse> {
  const context = buildContext(request.user_id);

  // Save signal
  const signal = {
    id: generateId('sig'),
    user_id: request.user_id,
    source_type: (request.metadata?.source_type as any) || 'system',
    signal_type: request.signal_type,
    raw_content: request.content,
    summary: `Signal: ${request.signal_type}`,
    sensitivity: 'medium' as const,
    confidence: 0.85,
    metadata_json: request.metadata || {},
    created_at: new Date().toISOString(),
  };
  addItem(db.signals, signal);

  const response = await adapter.processSignal(request, context);

  // Log agent run
  addItem(db.agent_runs, {
    id: generateId('run'),
    user_id: request.user_id,
    input_signal_id: signal.id,
    phase: response.phase,
    mode: response.mode,
    safety_status: response.safety_status,
    selected_action: response.selected_action,
    evidence_json: response.evidence,
    response_constraints_json: [],
    memory_updates_json: [],
    created_at: new Date().toISOString(),
  });

  // Handle escalation
  if (response.escalation_created) {
    createEscalationFromResponse(request.user_id, signal.id, response);
  }

  return response;
}

function createEscalationFromResponse(userId: string, signalId: string, response: AgentTurnResponse) {
  const escalation: EscalationEvent = {
    id: generateId('esc'),
    user_id: userId,
    trigger_signal_id: signalId,
    severity: response.safety_status,
    status: response.safety_status === 'crisis' ? 'simulated_alert_sent' : 'human_contact_suggested',
    summary: `Escalation triggered during ${response.mode} mode. Action: ${response.selected_action}`,
    recommended_action: response.safety_status === 'crisis'
      ? 'Immediate human contact recommended. Simulated alert sent to Care Circle.'
      : 'Gentle human check-in recommended. Notify trusted contact.',
    created_at: new Date().toISOString(),
    resolved_at: null,
  };
  addItem(db.escalation_events, escalation);

  // Create continuity packet
  const packet: ContinuityPacket = {
    id: generateId('cp'),
    user_id: userId,
    escalation_event_id: escalation.id,
    summary_for_agent: `Student experienced ${response.mode} mode event. Safety status: ${response.safety_status}.`,
    what_helped_json: [],
    what_worsened_json: ['Asking for score immediately', 'Productivity pressure', 'Comparisons'],
    future_response_rules_json: [
      'Do not ask for exam score first',
      'Avoid productivity pressure in first interaction',
      'Start future conversations gently',
      'Offer low-effort response options',
      'Check emotional state before academic topics',
    ],
    next_vulnerable_event: findByUserId(db.exams, userId).find(e => e.status === 'upcoming')?.name || 'Next exam',
    active: true,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  };
  addItem(db.continuity_packets, packet);
}

export function getAgentRuns(userId: string): AgentRun[] {
  return findByUserId(db.agent_runs, userId).sort(
    (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
  );
}
