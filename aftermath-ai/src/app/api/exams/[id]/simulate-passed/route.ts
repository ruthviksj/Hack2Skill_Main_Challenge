import { NextResponse } from 'next/server';
import { simulateExamPassed } from '@/lib/services/exam-service';

export async function POST(req: Request, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const exam = simulateExamPassed(id);
  if (!exam) return NextResponse.json({ error: 'Not found' }, { status: 404 });
  return NextResponse.json(exam);
}
