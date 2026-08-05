import { NextResponse } from 'next/server';
import { apiFetch } from '@/lib/api-client';
import { getAccessToken } from '@/lib/auth';

export async function POST(req: Request) {
  const token = await getAccessToken();
  if (!token) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });

  const body = await req.json();
  
  const res = await apiFetch('/api/voice/synthesize', {
    method: 'POST',
    body: JSON.stringify(body),
  }, token);
  
  const data = await res.json();
  return NextResponse.json(data, { status: res.status });
}
