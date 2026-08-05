import { NextRequest, NextResponse } from 'next/server';
import { setAuthCookies } from '@/lib/auth';

export async function POST(req: NextRequest) {
  const body = await req.json();

  // Call Supabase Auth API
  const response = await fetch(
    `${process.env.NEXT_PUBLIC_SUPABASE_URL}/auth/v1/token?grant_type=password`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        apikey: process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
      },
      body: JSON.stringify({
        email: body.email,
        password: body.password,
      }),
    }
  );

  if (!response.ok) {
    const error = await response.json();
    return NextResponse.json(
      { error: error.error_description || 'Login failed' },
      { status: response.status }
    );
  }

  const data = await response.json();

  // Set HttpOnly cookies
  await setAuthCookies(data.access_token, data.refresh_token);

  return NextResponse.json({
    user: data.user,
    redirect: '/dashboard',
  });
}
