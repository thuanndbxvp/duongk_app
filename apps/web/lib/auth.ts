/**
 * Auth helpers for Next.js BFF.
 */
import { cookies } from 'next/headers';
import { jwtDecode } from 'jwt-decode';
import { apiFetch } from '@/lib/api-client';

const ACCESS_TOKEN_COOKIE = 'sb-access-token';
const REFRESH_TOKEN_COOKIE = 'sb-refresh-token';

export interface User {
  sub: string;
  email: string;
  exp: number;
}

export async function getAccessToken(): Promise<string | null> {
  const cookieStore = await cookies();
  return cookieStore.get(ACCESS_TOKEN_COOKIE)?.value ?? null;
}

export async function getRefreshToken(): Promise<string | null> {
  const cookieStore = await cookies();
  return cookieStore.get(REFRESH_TOKEN_COOKIE)?.value ?? null;
}

export async function getUser(): Promise<User | null> {
  const token = await getAccessToken();
  if (!token) return null;
  
  try {
    return jwtDecode<User>(token);
  } catch {
    return null;
  }
}

export interface FullUser {
  email: string;
  full_name: string | null;
  avatar_url: string | null;
  tier: string;
  credits: number;
}

export async function getFullUser(): Promise<FullUser | null> {
  const token = await getAccessToken();
  if (!token) return null;

  // Dev mode: try decoding our own mock JWT first (carries email/name directly)
  if (token.startsWith('dev.') && token.endsWith('.mock')) {
    try {
      const payloadB64 = token.split('.')[1];
      const payload = JSON.parse(Buffer.from(payloadB64, 'base64').toString());
      return {
        email: payload.email,
        full_name: payload.full_name ?? null,
        avatar_url: null,
        tier: payload.tier ?? 'free',
        credits: payload.credits ?? 0,
      };
    } catch {
      // fallthrough to legacy mock
    }
  }

  // Also handle legacy base64 mock token
  try {
    const decoded = Buffer.from(token, 'base64').toString();
    if (decoded.includes('dev-mock-token')) {
      return {
        email: 'dev@local.test',
        full_name: 'Dev User',
        avatar_url: null,
        tier: 'pro',
        credits: 999,
      };
    }
  } catch {
    // ignore
  }

  try {
    const res = await apiFetch('/api/users/me', {}, token);
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

export async function setAuthCookies(accessToken: string, refreshToken: string) {
  const cookieStore = await cookies();
  const cookieOpts = {
    httpOnly: true,
    secure: process.env.NODE_ENV === 'production',
    sameSite: 'lax' as const,
    path: '/',
    maxAge: 60 * 60, // 1 hour
  };

  cookieStore.set(ACCESS_TOKEN_COOKIE, accessToken, cookieOpts);
  cookieStore.set(REFRESH_TOKEN_COOKIE, refreshToken, cookieOpts);
}

export async function clearAuthCookies() {
  const cookieStore = await cookies();
  cookieStore.delete(ACCESS_TOKEN_COOKIE);
  cookieStore.delete(REFRESH_TOKEN_COOKIE);
}
