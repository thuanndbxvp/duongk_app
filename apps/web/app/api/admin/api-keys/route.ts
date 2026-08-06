import { NextRequest, NextResponse } from 'next/server';
import { apiFetch } from '@/lib/api-client';
import { getAccessToken } from '@/lib/auth';

async function safeJson(response: Response): Promise<unknown> {
  const text = await response.text();
  if (!text) return {};
  try {
    return JSON.parse(text);
  } catch {
    return {};
  }
}

export async function GET(req: NextRequest) {
  const token = await getAccessToken();
  if (!token) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  const params = req.nextUrl.searchParams.toString();
  try {
    const response = await apiFetch(
      `/api/admin/api-keys${params ? `?${params}` : ''}`,
      {},
      token
    );
    const data = await safeJson(response);

    // Accept { keys: [...] } ; tolerate { items: [...] } or missing array.
    let keys: unknown[] = [];
    const candidate = (data as { keys?: unknown }).keys;
    if (Array.isArray(candidate)) {
      keys = candidate;
    } else {
      const items = (data as { items?: unknown }).items;
      if (Array.isArray(items)) keys = items;
    }
    return NextResponse.json({ keys, total: keys.length }, { status: response.status });
  } catch {
    return NextResponse.json({ keys: [], total: 0 }, { status: 200 });
  }
}

export async function POST(req: NextRequest) {
  const token = await getAccessToken();
  if (!token) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  const body = await req.json();
  try {
    const response = await apiFetch(
      '/api/admin/api-keys',
      {
        method: 'POST',
        body: JSON.stringify(body),
      },
      token
    );
    const data = await safeJson(response);
    return NextResponse.json(data, { status: response.status });
  } catch {
    return NextResponse.json({ error: 'Internal error' }, { status: 500 });
  }
}