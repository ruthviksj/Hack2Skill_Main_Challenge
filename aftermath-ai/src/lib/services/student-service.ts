import { db, generateId, findByUserId, addItem, DEMO_USER_ID, getDemoUser } from '../db';
import type { User } from '../types';

export function getCurrentUser(): User | undefined {
  return getDemoUser();
}
