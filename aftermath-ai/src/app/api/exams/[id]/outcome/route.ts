import { NextResponse } from 'next/server';
import { updateExamOutcome } from '@/lib/services/exam-service';

export async function PATCH(req: Request, { params }: { params: Promise<{ id: string }> }) {
  const body = await req.json();
  const { id } = await params;
  const exam = updateExamOutcome(id, body.actual_score);
  if (!exam) return NextResponse.json({ error: 'Not found' }, { status: 404 });
  return NextResponse.json(exam);
}
