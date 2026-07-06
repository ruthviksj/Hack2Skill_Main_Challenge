import { db, findByUserId, updateItem } from '../db';
import type { ContinuityPacket } from '../types';

export function getContinuityPackets(userId: string): ContinuityPacket[] {
  return findByUserId(db.continuity_packets, userId).sort(
    (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
  );
}

export function getActiveContinuityPacket(userId: string): ContinuityPacket | undefined {
  return findByUserId(db.continuity_packets, userId).find(p => p.active);
}
