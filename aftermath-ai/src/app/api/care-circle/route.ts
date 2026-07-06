import { NextResponse } from 'next/server';
import { getCareCircle, addCareCircleMember } from '@/lib/services/care-circle-service';
import { DEMO_USER_ID } from '@/lib/db';

export async function GET() {
  const circle = getCareCircle(DEMO_USER_ID);
  return NextResponse.json(circle);
}

export async function POST(req: Request) {
  const body = await req.json();
  const member = addCareCircleMember(DEMO_USER_ID, body);
  return NextResponse.json(member, { status: 201 });
}
