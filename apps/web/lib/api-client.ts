/**
 * FastAPI client with automatic JWT injection.
 */
const FASTAPI_URL = process.env.FASTAPI_URL || 'http://127.0.0.1:8000';

export async function apiFetch(
  path: string,
  options: RequestInit = {},
  accessToken?: string
): Promise<Response> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string>),
  };

  if (accessToken) {
    headers['Authorization'] = `Bearer ${accessToken}`;
  }

  return fetch(`${FASTAPI_URL}${path}`, {
    ...options,
    headers,
  });
}
