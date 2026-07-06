// ============================================================
// Aftermath AI — Agent Adapter Interface
// ============================================================
// This interface defines the contract between the app and the AI agent.
// The real Claude-built agent can be plugged in by implementing this interface.

import type {
  AgentTurnRequest, AgentTurnResponse,
  AgentSignalRequest, AgentMode, AgentPhase, SafetyStatus,
} from '../types';

export interface AgentAdapter {
  /**
   * Process a student chat/journal turn.
   * Returns the agent's response with mode, phase, safety info, and suggested actions.
   */
  processTurn(request: AgentTurnRequest, context: AgentContext): Promise<AgentTurnResponse>;

  /**
   * Process a non-chat signal (buddy concern, missed followup, system event).
   * Returns a summary response for internal processing.
   */
  processSignal(request: AgentSignalRequest, context: AgentContext): Promise<AgentTurnResponse>;
}

export interface AgentContext {
  /** Recent chat messages for conversation context */
  recentMessages: Array<{ role: string; content: string }>;
  /** Current exams and their statuses */
  exams: Array<{ name: string; status: string; exam_date: string; expected_score: string; actual_score: string | null }>;
  /** Active continuity packets (rules from past escalations) */
  continuityRules: string[];
  /** Current detected mode */
  currentMode: AgentMode;
  /** Current phase */
  currentPhase: AgentPhase;
  /** Current safety status */
  safetyStatus: SafetyStatus;
  /** Whether there are unresolved exams */
  hasMissingClosure: boolean;
  /** The missing closure exam name if any */
  missingClosureExam?: string;
}
