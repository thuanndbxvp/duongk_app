import { NextRequest, NextResponse } from 'next/server';
import { apiFetch } from '@/lib/api-client';
import { getAccessToken } from '@/lib/auth';

export async function GET(req: NextRequest) {
  const token = await getAccessToken();
  if (!token) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  const metric = req.nextUrl.searchParams.get('metric') || 'assistants';
  const limit = req.nextUrl.searchParams.get('limit') || '10';
  try {
    const response = await apiFetch(`/api/admin/analytics/top-creators?metric=${metric}&limit=${limit}`, {}, token);
    return NextResponse.json(await response.json(), { status: response.status });
  } catch {
    return NextResponse.json({ error: 'Internal error' }, { status: 500 });
  }
}