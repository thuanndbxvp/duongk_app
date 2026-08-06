import { NextRequest, NextResponse } from 'next/server';
import { setAuthCookies } from '@/lib/auth';

export async function POST(req: NextRequest) {
  const body = await req.json();

  // Dev mode: bypass Supabase when using placeholder URL
  if (process.env.NEXT_PUBLIC_SUPABASE_URL?.includes('xxx')) {
    console.warn('[DEV] Supabase URL is placeholder — using mock login');
    // Encode email + name into the mock JWT so getFullUser can recover them
    const payload = JSON.stringify({
      sub: 'dev-user',
      email: body.email,
      full_name: body.full_name ?? null,
      tier: 'pro',
      credits: 999,
      exp: Math.floor(Date.now() / 1000) + 3600,
    });
    const mockToken = `dev.${Buffer.from(payload).toString('base64')}.mock`;
    return NextResponse.json(
      {
        user: { id: 'dev-user', email: body.email },
        redirect: '/dashboard',
      },
      {
        headers: {
          'Set-Cookie': `sb-access-token=${mockToken}; Path=/; HttpOnly; SameSite=Lax`,
        },
      }
    );
  }

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
