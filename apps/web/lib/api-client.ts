/**
 * FastAPI client with automatic JWT injection.
 */
const FASTAPI_URL = process.env.FASTAPI_URL || 'http://127.0.0.1:8001';
const DEFAULT_TIMEOUT_MS = 10_000;

export async function apiFetch(
  path: string,
  options: RequestInit = {},
  accessToken?: string,
  timeoutMs: number = DEFAULT_TIMEOUT_MS
): Promise<Response> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string>),
  };

  if (accessToken) {
    headers['Authorization'] = `Bearer ${accessToken}`;
  }

  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(`timeout ${timeoutMs}ms`), timeoutMs);

  try {
    return await fetch(`${FASTAPI_URL}${path}`, {
      ...options,
      headers,
      signal: controller.signal,
      cache: 'no-store',
    });
  } finally {
    clearTimeout(timer);
  }
}
