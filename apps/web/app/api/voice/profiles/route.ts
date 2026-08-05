import { NextResponse } from 'next/server';
import { apiFetch } from '@/lib/api-client';
import { getAccessToken } from '@/lib/auth';

export async function GET() {
  const token = await getAccessToken();
  if (!token) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });

  const res = await apiFetch('/api/voice/profiles', {}, token);
  const data = await res.json();
  return NextResponse.json(data, { status: res.status });
}

export async function POST(req: Request) {
  const token = await getAccessToken();
  if (!token) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });

  const formData = await req.formData();
  
  // Create a new request to forward the form data
  const res = await apiFetch('/api/voice/profiles', {
    method: 'POST',
    // Do not set Content-Type header manually when sending FormData,
    // fetch will automatically set it with the correct boundary
    headers: {},
    body: formData as any,
  }, token);
  
  const data = await res.json();
  return NextResponse.json(data, { status: res.status });
}
