import { NextResponse } from 'next/server';
import { getEscalations } from '@/lib/services/escalation-service';
import { DEMO_USER_ID } from '@/lib/db';

export async function GET() {
  const escalations = getEscalations(DEMO_USER_ID);
  return NextResponse.json(escalations);
}
