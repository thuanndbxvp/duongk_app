import { NextResponse } from 'next/server';
import { apiFetch } from '@/lib/api-client';

export async function GET() {
  try {
    // /credits/pricing là public — không cần token
    const response = await apiFetch('/api/credits/pricing', {}, undefined);
    const data = await response.json();
    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    return NextResponse.json({ error: 'Internal error' }, { status: 500 });
  }
}