import { NextRequest, NextResponse } from 'next/server';
import { apiFetch } from '@/lib/api-client';
import { getAccessToken } from '@/lib/auth';

export async function GET(req: NextRequest) {
  const token = await getAccessToken();
  if (!token) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  const weeks = req.nextUrl.searchParams.get('weeks') || '8';
  try {
    const response = await apiFetch(
      `/api/admin/analytics/cohort?weeks=${weeks}`,
      {},
      token
    );
    const text = await response.text();
    let data: unknown;
    try {
      data = text ? JSON.parse(text) : {};
    } catch {
      data = {};
    }

    // Backend may return either { cohorts: [...] } or an error payload.
    // Make sure the shape is stable for the admin UI so empty / failure
    // responses don't crash the dashboard with "cannot read cohorts.length".
    if (
      !data ||
      typeof data !== 'object' ||
      !Array.isArray((data as { cohorts?: unknown }).cohorts)
    ) {
      data = { cohorts: [], weeks: Number(weeks) };
    }

    return NextResponse.json(data, { status: response.status });
  } catch {
    return NextResponse.json({ cohorts: [], weeks: Number(weeks) }, { status: 200 });
  }
}