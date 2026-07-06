import { NextResponse } from 'next/server';
import { resetDatabase } from '@/lib/db';

export async function POST() {
  resetDatabase();
  return NextResponse.json({ success: true, message: 'Demo state reset' });
}
