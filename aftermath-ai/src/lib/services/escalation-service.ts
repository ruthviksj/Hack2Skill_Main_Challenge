import { db, generateId, findByUserId, updateItem } from '../db';
import type { EscalationEvent, PostEscalationUpdateRequest, ContinuityPacket } from '../types';

export function getEscalations(userId: string): EscalationEvent[] {
  return findByUserId(db.escalation_events, userId).sort(
    (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
  );
}

export function updateEscalationStatus(escalationId: string, status: EscalationEvent['status']): EscalationEvent | null {
  return updateItem(db.escalation_events, escalationId, {
    status,
    resolved_at: status === 'resolved' ? new Date().toISOString() : null,
  });
}
