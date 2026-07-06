import { NextResponse } from 'next/server';
import { getContinuityPackets, getActiveContinuityPacket } from '@/lib/services/continuity-service';
import { DEMO_USER_ID } from '@/lib/db';

export async function GET(req: Request) {
  const { searchParams } = new URL(req.url);
  const activeOnly = searchParams.get('active') === 'true';

  if (activeOnly) {
    const active = getActiveContinuityPacket(DEMO_USER_ID);
    return NextResponse.json(active || null);
  }

  const packets = getContinuityPackets(DEMO_USER_ID);
  return NextResponse.json(packets);
}
