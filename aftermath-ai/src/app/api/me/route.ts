import { NextResponse } from 'next/server';
import { getCurrentUser } from '@/lib/services/student-service';

export async function GET() {
  const user = getCurrentUser();
  if (!user) return NextResponse.json({ error: 'No demo user' }, { status: 404 });
  return NextResponse.json(user);
}
