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
  try {
    const response = await apiFetch('/api/admin/routing-config', {}, token);
    const data = await safeJson(response);

    // Accept { configs: [...] } ; tolerate { items: [...] } or missing array.
    let configs: unknown[] = [];
    const candidate = (data as { configs?: unknown }).configs;
    if (Array.isArray(candidate)) {
      configs = candidate;
    } else {
      const items = (data as { items?: unknown }).items;
      if (Array.isArray(items)) configs = items;
    }
    return NextResponse.json({ configs, total: configs.length }, { status: response.status });
  } catch {
    return NextResponse.json({ configs: [], total: 0 }, { status: 200 });
  }
}