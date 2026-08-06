import { NextRequest, NextResponse } from 'next/server';
import { apiFetch } from '@/lib/api-client';
import { getAccessToken } from '@/lib/auth';

export async function GET(req: NextRequest, { params }: { params: { id: string } }) {
  const token = await getAccessToken();
  if (!token) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });

  const response = await apiFetch(`/api/projects/${params.id}`, {}, token);
  const data = await response.json();
  return NextResponse.json(data, { status: response.status });
}
