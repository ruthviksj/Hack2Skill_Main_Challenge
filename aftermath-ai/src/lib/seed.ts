// ============================================================
// Aftermath AI — Demo Seed Data
// ============================================================

import type { DBStore } from './db';

export function seedDatabase(store: DBStore): void {
  const now = new Date();
  const sevenDaysAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
  const fourteenDaysFromNow = new Date(now.getTime() + 14 * 24 * 60 * 60 * 1000);

  // --- Demo Student ---
  store.users.push({
    id: 'user_demo_001',
    name: 'Arjun Mehta',
    email: 'arjun@demo.aftermath.ai',
    role: 'student',
    preferred_tone: 'warm',
    preferred_language: 'en',
    avatar_emoji: '🎓',
    created_at: new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000).toISOString(),
  });

  // --- Exams ---
  // Exam 1: Past exam with outcome_missing (the key demo scenario)
  store.exams.push({
    id: 'exam_001',
    user_id: 'user_demo_001',
    name: 'GMAT Mock Test 3',
    exam_type: 'Mock Test',
    exam_date: sevenDaysAgo.toISOString(),
    importance: 'high',
    expected_score: '680+',
    expected_confidence: 75,
    actual_score: null,
    status: 'outcome_missing',
    created_at: new Date(sevenDaysAgo.getTime() - 3 * 24 * 60 * 60 * 1000).toISOString(),
    updated_at: sevenDaysAgo.toISOString(),
  });

  // Exam 2: Upcoming exam
  store.exams.push({
    id: 'exam_002',
    user_id: 'user_demo_001',
    name: 'GMAT Official Exam',
    exam_type: 'Final Exam',
    exam_date: fourteenDaysFromNow.toISOString(),
    importance: 'critical',
    expected_score: '700+',
    expected_confidence: 60,
    actual_score: null,
    status: 'upcoming',
    created_at: now.toISOString(),
    updated_at: now.toISOString(),
  });

  // --- Care Circle Members ---
  store.care_circle_members.push({
    id: 'cc_001',
    user_id: 'user_demo_001',
    name: 'Riya Sharma',
    relationship: 'Study Buddy',
    role: 'buddy',
    can_submit_concern: true,
    can_receive_emergency_alert: false,
    can_view_private_chat: false,
    avatar_emoji: '👩‍🎓',
    created_at: new Date(now.getTime() - 15 * 24 * 60 * 60 * 1000).toISOString(),
  });

  store.care_circle_members.push({
    id: 'cc_002',
    user_id: 'user_demo_001',
    name: 'Sunita Mehta',
    relationship: 'Mother',
    role: 'parent',
    can_submit_concern: false,
    can_receive_emergency_alert: true,
    can_view_private_chat: false,
    avatar_emoji: '👩',
    created_at: new Date(now.getTime() - 25 * 24 * 60 * 60 * 1000).toISOString(),
  });

  store.care_circle_members.push({
    id: 'cc_003',
    user_id: 'user_demo_001',
    name: 'Dr. Ananya Iyer',
    relationship: 'School Counsellor',
    role: 'counsellor',
    can_submit_concern: true,
    can_receive_emergency_alert: true,
    can_view_private_chat: false,
    avatar_emoji: '👩‍⚕️',
    created_at: new Date(now.getTime() - 20 * 24 * 60 * 60 * 1000).toISOString(),
  });

  // --- Initial signal: Missing followup detected by system ---
  store.signals.push({
    id: 'signal_001',
    user_id: 'user_demo_001',
    source_type: 'system',
    signal_type: 'missed_followup',
    raw_content: 'GMAT Mock Test 3 occurred 7 days ago. No outcome update received. Expected score was 680+.',
    summary: 'Missing closure: GMAT Mock Test 3',
    sensitivity: 'medium',
    confidence: 0.95,
    metadata_json: { exam_id: 'exam_001', days_since_exam: 7 },
    created_at: now.toISOString(),
  });
}
