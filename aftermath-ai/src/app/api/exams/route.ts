import { NextResponse } from 'next/server';
import { getExams, createExam } from '@/lib/services/exam-service';
import { DEMO_USER_ID } from '@/lib/db';

export async function GET() {
  const exams = getExams(DEMO_USER_ID);
  return NextResponse.json(exams);
}

export async function POST(req: Request) {
  const body = await req.json();
  const exam = createExam(DEMO_USER_ID, body);
  return NextResponse.json(exam, { status: 201 });
}
