// ============================================================
// Aftermath AI — Core TypeScript Types
// ============================================================

// --- Enums ---

export type UserRole = 'student' | 'buddy' | 'parent' | 'counsellor';

export type ExamStatus = 'upcoming' | 'completed' | 'outcome_missing' | 'outcome_reported';

export type ExamImportance = 'low' | 'medium' | 'high' | 'critical';

export type SignalSourceType = 'student' | 'buddy' | 'parent' | 'counsellor' | 'system';

export type SignalType =
  | 'chat'
  | 'journal'
  | 'mood_log'
  | 'exam_created'
  | 'score_update'
  | 'missed_followup'
  | 'buddy_concern'
  | 'safety_concern'
  | 'post_escalation_update';

export type ChatRole = 'user' | 'assistant' | 'system';

export type AgentMode = 'normal' | 'aftermath' | 'protect_next_paper' | 'safety';

export type AgentPhase = 'phase_0' | 'phase_1' | 'phase_2' | 'phase_3' | 'phase_4';

export type SafetyStatus = 'safe' | 'monitoring' | 'concern' | 'urgent' | 'crisis';

export type EscalationStatus = 'created' | 'human_contact_suggested' | 'simulated_alert_sent' | 'resolved';

export type Sensitivity = 'low' | 'medium' | 'high' | 'critical';

export type MoodLevel = 'great' | 'okay' | 'low' | 'struggling' | 'crisis';

// --- Entities ---

export interface User {
  id: string;
  name: string;
  email: string;
  role: UserRole;
  preferred_tone: string;
  preferred_language: string;
  avatar_emoji: string;
  created_at: string;
}

export interface Exam {
  id: string;
  user_id: string;
  name: string;
  exam_type: string;
  exam_date: string;
  importance: ExamImportance;
  expected_score: string;
  expected_confidence: number; // 0-100
  actual_score: string | null;
  status: ExamStatus;
  created_at: string;
  updated_at: string;
}

export interface Signal {
  id: string;
  user_id: string;
  source_type: SignalSourceType;
  signal_type: SignalType;
  raw_content: string;
  summary: string;
  sensitivity: Sensitivity;
  confidence: number;
  metadata_json: Record<string, unknown>;
  created_at: string;
}

export interface ChatMessage {
  id: string;
  user_id: string;
  role: ChatRole;
  content: string;
  mode: AgentMode;
  phase: AgentPhase;
  suggested_buttons?: string[];
  created_at: string;
}

export interface CareCircleMember {
  id: string;
  user_id: string;
  name: string;
  relationship: string;
  role: UserRole;
  can_submit_concern: boolean;
  can_receive_emergency_alert: boolean;
  can_view_private_chat: boolean;
  avatar_emoji: string;
  created_at: string;
}

export interface EscalationEvent {
  id: string;
  user_id: string;
  trigger_signal_id: string;
  severity: SafetyStatus;
  status: EscalationStatus;
  summary: string;
  recommended_action: string;
  created_at: string;
  resolved_at: string | null;
}

export interface ContinuityPacket {
  id: string;
  user_id: string;
  escalation_event_id: string;
  summary_for_agent: string;
  what_helped_json: string[];
  what_worsened_json: string[];
  future_response_rules_json: string[];
  next_vulnerable_event: string;
  active: boolean;
  created_at: string;
  updated_at: string;
}

export interface AgentRun {
  id: string;
  user_id: string;
  input_signal_id: string;
  phase: AgentPhase;
  mode: AgentMode;
  safety_status: SafetyStatus;
  selected_action: string;
  evidence_json: string[];
  response_constraints_json: string[];
  memory_updates_json: string[];
  created_at: string;
}

// --- API Request/Response Types ---

export interface CreateExamRequest {
  name: string;
  exam_type: string;
  exam_date: string;
  importance: ExamImportance;
  expected_score: string;
  expected_confidence: number;
}

export interface UpdateOutcomeRequest {
  actual_score: string;
  how_it_went?: string;
}

export interface AgentTurnRequest {
  user_id: string;
  input_type: 'chat' | 'journal';
  content: string;
  related_exam_id?: string;
}

export interface AgentTurnResponse {
  assistant_response: string;
  phase: AgentPhase;
  mode: AgentMode;
  safety_status: SafetyStatus;
  selected_action: string;
  evidence: string[];
  suggested_buttons: string[];
  escalation_created: boolean;
  continuity_updated: boolean;
}

export interface AgentSignalRequest {
  user_id: string;
  signal_type: SignalType;
  content: string;
  metadata?: Record<string, unknown>;
}

export interface BuddyConcernRequest {
  user_id: string;
  buddy_id: string;
  observed_behavior: string;
  direct_quote: string;
  urgency: 'low' | 'medium' | 'high' | 'critical';
  observed_or_inferred: 'observed' | 'inferred';
  safety_status: SafetyStatus;
  what_tried: string;
}

export interface BuddyConcernResponse {
  signal_id: string;
  safety_gate_result: SafetyStatus;
  escalation_created: boolean;
  agent_summary: string;
}

export interface PostEscalationUpdateRequest {
  current_state: string;
  what_helped: string[];
  what_worsened: string[];
  future_response_rules: string[];
  next_vulnerable_event: string;
}
