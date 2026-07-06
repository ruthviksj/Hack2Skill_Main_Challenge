import { db, generateId, findByUserId, addItem } from '../db';
import type { CareCircleMember, UserRole } from '../types';

export function getCareCircle(userId: string): CareCircleMember[] {
  return findByUserId(db.care_circle_members, userId);
}

export function addCareCircleMember(userId: string, data: Omit<CareCircleMember, 'id' | 'user_id' | 'created_at'>): CareCircleMember {
  const member: CareCircleMember = {
    ...data,
    id: generateId('cc'),
    user_id: userId,
    created_at: new Date().toISOString(),
  };
  return addItem(db.care_circle_members, member);
}
