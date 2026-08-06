/**
 * Defensive fetch helpers — avoid the "setState received an object" crash when
 * a backend proxy returns `{ error: ... }` or an empty body.
 *
 * All admin pages should use these instead of hand-rolling
 * `fetch().then(r => r.json()).then(setState)` chains.
 */
'use client';

import { useCallback, useEffect, useState } from 'react';

type Setter<T> = (value: T) => void;

/** Convert any value to a safe array. Accepts: array, undefined, null, object. */
function toArray<T>(value: unknown): T[] {
  if (Array.isArray(value)) return value as T[];
  return [];
}

/** Resolve a key inside a payload. Special key '_self' returns the payload as-is. */
function pickKey(payload: unknown, key: string): unknown {
  if (key === '_self') return payload;
  if (payload && typeof payload === 'object') {
    return (payload as Record<string, unknown>)[key];
  }
  return undefined;
}

/** Build a query string from a plain object, dropping null/undefined/empty. */
export function buildQuery(params: Record<string, unknown>): string {
  const usp = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value === null || value === undefined || value === '') continue;
    usp.set(key, String(value));
  }
  const s = usp.toString();
  return s ? `?${s}` : '';
}

/**
 * Fetch a paginated list with `{ items: T[], total: number }` shape (or
 * tolerates `{ <custom_key>: T[] }` via the `key` option).
 *
 * @param url        Absolute or relative URL.
 * @param deps       useEffect deps (typically filter/page state).
 * @param key        Key holding the array in the response (default: 'items').
 * @param totalKey   Key holding the total count (default: 'total').
 */
export function useArrayFetch<T>(url: string | null, deps: unknown[], key = 'items', totalKey = 'total') {
  const [data, setData] = useState<T[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(() => {
    if (!url) {
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    fetch(url)
      .then(async (r) => {
        if (!r.ok) {
          const text = await r.text().catch(() => '');
          throw new Error(`HTTP ${r.status}${text ? `: ${text.slice(0, 200)}` : ''}`);
        }
        return r.json();
      })
      .then((payload) => {
        const list = toArray<T>(pickKey(payload, key));
        setData(list);
        const totalVal = pickKey(payload, totalKey);
        setTotal(typeof totalVal === 'number' ? totalVal : list.length);
      })
      .catch((err: Error) => {
        setError(err.message);
        setData([]);
        setTotal(0);
      })
      .finally(() => setLoading(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  useEffect(() => {
    load();
  }, [load]);

  return { data, total, loading, error, refresh: load };
}

/**
 * Fetch a single object. Returns null on error/empty.
 *
 * @param url  Absolute or relative URL.
 * @param deps useEffect deps.
 */
export function useObjectFetch<T>(url: string | null, deps: unknown[]) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(() => {
    if (!url) {
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    fetch(url)
      .then(async (r) => {
        if (!r.ok) {
          const text = await r.text().catch(() => '');
          throw new Error(`HTTP ${r.status}${text ? `: ${text.slice(0, 200)}` : ''}`);
        }
        return r.json();
      })
      .then((payload) => setData((payload ?? null) as T | null))
      .catch((err: Error) => {
        setError(err.message);
        setData(null);
      })
      .finally(() => setLoading(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  useEffect(() => {
    load();
  }, [load]);

  return { data, loading, error, refresh: load, setData: setData as Setter<T | null> };
}

/**
 * Imperative helper — useful when you want to refetch after a mutation
 * (e.g. create / delete) without re-typing the same fetch + normalize.
 *
 * Returns `{ items, total }` even on error.
 */
export async function fetchArray<T>(url: string, key = 'items', totalKey = 'total'): Promise<{ items: T[]; total: number }> {
  try {
    const res = await fetch(url);
    if (!res.ok) return { items: [], total: 0 };
    const payload = await res.json().catch(() => ({}));
    const items = toArray<T>(pickKey(payload, key));
    const totalVal = pickKey(payload, totalKey);
    return { items, total: typeof totalVal === 'number' ? totalVal : items.length };
  } catch {
    return { items: [], total: 0 };
  }
}
