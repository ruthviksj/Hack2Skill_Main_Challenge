import { NextResponse } from 'next/server';
import { updateEscalationStatus } from '@/lib/services/escalation-service';

export async function PATCH(req: Request, { params }: { params: Promise<{ id: string }> }) {
  const body = await req.json();
  const { id } = await params;
  const escalation = updateEscalationStatus(id, body.status);
  if (!escalation) return NextResponse.json({ error: 'Not found' }, { status: 404 });
  return NextResponse.json(escalation);
}
