// ============================================================
// Aftermath AI — In-Memory Database Store
// ============================================================

import {
  User, Exam, Signal, ChatMessage, CareCircleMember,
  EscalationEvent, ContinuityPacket, AgentRun,
} from './types';
import { seedDatabase } from './seed';

// --- Store Shape ---
export interface DBStore {
  users: User[];
  exams: Exam[];
  signals: Signal[];
  chat_messages: ChatMessage[];
  care_circle_members: CareCircleMember[];
  escalation_events: EscalationEvent[];
  continuity_packets: ContinuityPacket[];
  agent_runs: AgentRun[];
}

// --- Global In-Memory Store (survives hot-reload in dev via globalThis) ---
const globalForDb = globalThis as unknown as { __db: DBStore };

function createEmptyStore(): DBStore {
  return {
    users: [],
    exams: [],
    signals: [],
    chat_messages: [],
    care_circle_members: [],
    escalation_events: [],
    continuity_packets: [],
    agent_runs: [],
  };
}

if (!globalForDb.__db) {
  globalForDb.__db = createEmptyStore();
  seedDatabase(globalForDb.__db);
}

export const db = globalForDb.__db;

// --- ID Generator ---
let counter = 1000;
export function generateId(prefix: string = ''): string {
  counter++;
  return `${prefix}${prefix ? '_' : ''}${Date.now()}_${counter}`;
}

// --- CRUD Helpers ---

export function findById<T extends { id: string }>(collection: T[], id: string): T | undefined {
  return collection.find(item => item.id === id);
}

export function findByUserId<T extends { user_id: string }>(collection: T[], userId: string): T[] {
  return collection.filter(item => item.user_id === userId);
}

export function addItem<T>(collection: T[], item: T): T {
  collection.push(item);
  return item;
}

export function updateItem<T extends { id: string }>(collection: T[], id: string, updates: Partial<T>): T | null {
  const index = collection.findIndex(item => item.id === id);
  if (index === -1) return null;
  collection[index] = { ...collection[index], ...updates };
  return collection[index];
}

export function resetDatabase(): void {
  globalForDb.__db = createEmptyStore();
  seedDatabase(globalForDb.__db);
  // Reassign the module-level export
  Object.assign(db, globalForDb.__db);
}

// --- Demo User Helper ---
export const DEMO_USER_ID = 'user_demo_001';

export function getDemoUser(): User | undefined {
  return findById(db.users, DEMO_USER_ID);
}
