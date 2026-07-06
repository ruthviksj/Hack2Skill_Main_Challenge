// ============================================================
// Aftermath AI — Exam Service
// ============================================================

import { db, generateId, findById, findByUserId, addItem, updateItem, DEMO_USER_ID } from '../db';
import type { Exam, CreateExamRequest, Signal } from '../types';

export function getExams(userId: string): Exam[] {
  return findByUserId(db.exams, userId).sort(
    (a, b) => new Date(a.exam_date).getTime() - new Date(b.exam_date).getTime()
  );
}

export function getExam(examId: string): Exam | undefined {
  return findById(db.exams, examId);
}

export function createExam(userId: string, data: CreateExamRequest): Exam {
  const now = new Date().toISOString();
  const exam: Exam = {
    id: generateId('exam'),
    user_id: userId,
    name: data.name,
    exam_type: data.exam_type,
    exam_date: data.exam_date,
    importance: data.importance,
    expected_score: data.expected_score,
    expected_confidence: data.expected_confidence,
    actual_score: null,
    status: new Date(data.exam_date) < new Date() ? 'outcome_missing' : 'upcoming',
    created_at: now,
    updated_at: now,
  };
  addItem(db.exams, exam);

  // Create signal for exam creation
  addItem(db.signals, {
    id: generateId('sig'),
    user_id: userId,
    source_type: 'student',
    signal_type: 'exam_created',
    raw_content: `Created exam: ${data.name} on ${data.exam_date}`,
    summary: `New exam: ${data.name}`,
    sensitivity: 'low',
    confidence: 1.0,
    metadata_json: { exam_id: exam.id },
    created_at: now,
  });

  return exam;
}

export function updateExamOutcome(examId: string, actualScore: string): Exam | null {
  const now = new Date().toISOString();
  const exam = updateItem(db.exams, examId, {
    actual_score: actualScore,
    status: 'outcome_reported' as const,
    updated_at: now,
  });

  if (exam) {
    addItem(db.signals, {
      id: generateId('sig'),
      user_id: exam.user_id,
      source_type: 'student',
      signal_type: 'score_update',
      raw_content: `Updated exam result: ${exam.name} — ${actualScore}`,
      summary: `Score updated: ${exam.name}`,
      sensitivity: 'medium',
      confidence: 1.0,
      metadata_json: { exam_id: examId, actual_score: actualScore },
      created_at: now,
    });
  }

  return exam;
}

export function simulateExamPassed(examId: string): Exam | null {
  const now = new Date().toISOString();
  const exam = findById(db.exams, examId);
  if (!exam) return null;

  // Set exam date to 7 days ago and status to outcome_missing
  const sevenDaysAgo = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString();
  const updated = updateItem(db.exams, examId, {
    exam_date: sevenDaysAgo,
    status: 'outcome_missing' as const,
    updated_at: now,
  });

  if (updated) {
    // Create missing followup signal
    addItem(db.signals, {
      id: generateId('sig'),
      user_id: updated.user_id,
      source_type: 'system',
      signal_type: 'missed_followup',
      raw_content: `${updated.name} occurred 7 days ago. No outcome update received. Expected score was ${updated.expected_score}.`,
      summary: `Missing closure: ${updated.name}`,
      sensitivity: 'medium',
      confidence: 0.95,
      metadata_json: { exam_id: examId, days_since_exam: 7 },
      created_at: now,
    });
  }

  return updated;
}

export function getMissingClosureExams(userId: string): Exam[] {
  return findByUserId(db.exams, userId).filter(e => e.status === 'outcome_missing');
}
