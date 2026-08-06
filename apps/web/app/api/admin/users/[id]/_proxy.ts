/**
 * Common proxy helper used by every /api/admin/users/{id}/* route.
 * Handles auth + body forwarding + error mapping in one place.
 */
import { NextRequest, NextResponse } from 'next/server';
import { apiFetch } from '@/lib/api-client';
import { getAccessToken } from '@/lib/auth';

type HttpMethod = 'POST' | 'PATCH' | 'DELETE';

export async function proxyAdminUserAction(
  req: NextRequest,
  params: Promise<{ id: string }>,
  method: HttpMethod,
  backendPath: string,
): Promise<NextResponse> {
  const token = await getAccessToken();
  if (!token) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }
  const { id } = await params;
  let body: string | undefined;
  if (method !== 'DELETE') {
    try {
      body = JSON.stringify(await req.json());
    } catch {
      body = undefined;
    }
  }
  try {
    const response = await apiFetch(
      backendPath.replace('{id}', id),
      {
        method,
        ...(body ? { body } : {}),
      },
      token,
    );
    const text = await response.text();
    let data: unknown = null;
    try {
      data = text ? JSON.parse(text) : null;
    } catch {
      data = text;
    }
    return NextResponse.json(data, { status: response.status });
  } catch {
    return NextResponse.json({ error: 'Internal error' }, { status: 500 });
  }
}
