import { NextResponse } from 'next/server';
import { processAgentSignal } from '@/lib/services/agent-service';
import { DEMO_USER_ID } from '@/lib/db';

export async function POST(req: Request) {
  const body = await req.json();
  const response = await processAgentSignal({ ...body, user_id: DEMO_USER_ID });
  return NextResponse.json(response);
}
