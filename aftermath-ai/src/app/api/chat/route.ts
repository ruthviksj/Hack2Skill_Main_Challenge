import { NextResponse } from 'next/server';
import { db, findByUserId, DEMO_USER_ID } from '@/lib/db';

export async function GET() {
  const messages = findByUserId(db.chat_messages, DEMO_USER_ID).sort(
    (a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
  );
  return NextResponse.json(messages);
}
