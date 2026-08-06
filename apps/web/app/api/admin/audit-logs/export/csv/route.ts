import { NextRequest, NextResponse } from 'next/server';
import { apiFetch } from '@/lib/api-client';
import { getAccessToken } from '@/lib/auth';

export async function GET(req: NextRequest) {
  const token = await getAccessToken();
  if (!token) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  const params = req.nextUrl.searchParams.toString();
  try {
    const response = await apiFetch(`/api/admin/audit-logs/export/csv${params ? `?${params}` : ''}`, {}, token);
    const blob = await response.blob();
    return new NextResponse(blob, {
      status: response.status,
      headers: {
        'Content-Type': response.headers.get('Content-Type') || 'text/csv',
        'Content-Disposition': response.headers.get('Content-Disposition') || 'attachment',
      },
    });
  } catch {
    return NextResponse.json({ error: 'Internal error' }, { status: 500 });
  }
}