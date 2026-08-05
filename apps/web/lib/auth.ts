/**
 * Auth helpers for Next.js BFF.
 */
import { cookies } from 'next/headers';
import { jwtDecode } from 'jwt-decode';

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
