import { NextRequest, NextResponse } from 'next/server';
import { jwtDecode } from 'jwt-decode';

const ACCESS_TOKEN_COOKIE = 'sb-access-token';

const isDevMock = () =>
  process.env.NEXT_PUBLIC_SUPABASE_URL?.includes('xxx') ?? false;

interface SessionPayload {
  sub: string;
  email?: string;
  exp: number;
  role?: string;
}

async function getSessionFromCookies(
  request: NextRequest
): Promise<{ userId: string; role: string } | null> {
  const token = request.cookies.get(ACCESS_TOKEN_COOKIE)?.value;
  if (!token) return null;

  // Dev mock token: dev.<base64 payload>.mock
  if (token.startsWith('dev.') && token.endsWith('.mock')) {
    try {
      const payloadB64 = token.split('.')[1];
      const payload = JSON.parse(
        Buffer.from(payloadB64, 'base64').toString()
      ) as SessionPayload;
      if (!payload.exp || payload.exp * 1000 < Date.now()) return null;
      return {
        userId: payload.sub ?? 'dev-user',
        role: payload.role ?? 'user',
      };
    } catch {
      return null;
    }
  }

  // Real Supabase JWT
  try {
    const decoded = jwtDecode<SessionPayload>(token);
    if (!decoded.exp || decoded.exp * 1000 < Date.now()) return null;

    // Fetch role from Supabase REST
    const res = await fetch(
      `${process.env.NEXT_PUBLIC_SUPABASE_URL}/rest/v1/users?id=eq.${decoded.sub}&select=role`,
      {
        headers: {
          apikey: process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
          Authorization: `Bearer ${token}`,
        },
      }
    );
    if (!res.ok) return null;
    const rows = await res.json();
    return {
      userId: decoded.sub,
      role: rows?.[0]?.role ?? 'user',
    };
  } catch {
    return null;
  }
}

export async function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Chỉ apply cho /admin/* và /api/admin/*
  if (!pathname.startsWith('/admin') && !pathname.startsWith('/api/admin')) {
    return NextResponse.next();
  }

  const session = await getSessionFromCookies(request);

  // Chưa login → redirect to /login (giữ `next` để quay lại)
  if (!session) {
    const loginUrl = new URL('/login', request.url);
    loginUrl.searchParams.set('next', pathname);
    return NextResponse.redirect(loginUrl);
  }

  if (!['admin', 'super_admin'].includes(session.role)) {
    return NextResponse.redirect(new URL('/403', request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: ['/admin/:path*', '/api/admin/:path*'],
};