import { NextResponse } from 'next/server';
import { getAgentRuns } from '@/lib/services/agent-service';
import { DEMO_USER_ID } from '@/lib/db';

export async function GET() {
  const runs = getAgentRuns(DEMO_USER_ID);
  return NextResponse.json(runs);
}
