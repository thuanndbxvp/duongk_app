import { NextRequest, NextResponse } from 'next/server';
import { apiFetch } from '../../../../../lib/api-client';
import { getAccessToken } from '../../../../../lib/auth';

export async function GET(
  _req: NextRequest,
  { params }: { params: Promise<{ assistant_id: string }> }
) {
  const token = await getAccessToken();
  if (!token) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  const { assistant_id } = await params;

  try {
    const response = await apiFetch(
      `/api/ideas/${assistant_id}`,
      {},
      token
    );
    const data = await response.json();
    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    return NextResponse.json({ error: 'Internal error' }, { status: 500 });
  }
}
