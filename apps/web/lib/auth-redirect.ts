/**
 * Server-side: if user already has a valid session, redirect to the
 * appropriate landing page (admin panel for admin/super_admin, else
 * dashboard). Used by the /login route to prevent the "logged-in user
 * sees the login form" anti-pattern.
 */
import { redirect } from 'next/navigation';
import { jwtDecode } from 'jwt-decode';
import { getAccessToken } from '@/lib/auth';

const ACCESS_TOKEN_COOKIE = 'sb-access-token';

interface SessionPayload {
  sub: string;
  email?: string;
  exp: number;
  role?: string;
}

export async function redirectIfAuthenticated(nextPath?: string): Promise<void> {
  const token = await getAccessToken();
  if (!token) return;

  let payload: SessionPayload | null = null;

  // Dev mock token format: dev.<base64>.mock
  if (token.startsWith('dev.') && token.endsWith('.mock')) {
    try {
      const b64 = token.split('.')[1];
      payload = JSON.parse(Buffer.from(b64, 'base64').toString());
    } catch {
      payload = null;
    }
  } else {
    // Real Supabase JWT
    try {
      payload = jwtDecode<SessionPayload>(token);
    } catch {
      payload = null;
    }
  }

  if (!payload?.exp || payload.exp * 1000 < Date.now()) return;

  // If caller passed ?next=, honor it (admin flow uses ?next=/admin)
  if (nextPath && nextPath !== '/login') {
    redirect(nextPath);
  }

  // Default landing per role
  const role = payload.role ?? 'user';
  if (role === 'admin' || role === 'super_admin') {
    redirect('/admin');
  }
  redirect('/dashboard');
}