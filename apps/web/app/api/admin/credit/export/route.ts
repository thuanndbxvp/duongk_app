import { NextRequest, NextResponse } from 'next/server';
import { apiFetch } from '@/lib/api-client';
import { getAccessToken } from '@/lib/auth';

export async function GET(req: NextRequest) {
  const token = await getAccessToken();
  if (!token) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }
  const params = req.nextUrl.searchParams.toString();
  try {
    const response = await apiFetch(
      `/api/admin/credit/export${params ? `?${params}` : ''}`,
      {},
      token,
    );
    // Backend returns CSV text. Stream it back preserving content-type.
    const text = await response.text();
    return new NextResponse(text, {
      status: response.status,
      headers: {
        'Content-Type': response.headers.get('content-type') || 'text/csv',
        'Content-Disposition':
          response.headers.get('content-disposition') ||
          'attachment; filename="credit-ledger.csv"',
      },
    });
  } catch {
    return NextResponse.json({ error: 'Internal error' }, { status: 500 });
  }
}
