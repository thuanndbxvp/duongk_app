/**
 * Analysis API client helper — Hidden Features P2.
 * Uses Promise.allSettled for per-tab error tolerance.
 */
import { apiFetch } from '@/lib/api-client';

export interface AnalysisData {
  nlp: unknown | null;
  llm: unknown | null;
  deterministic: unknown | null;
  insights: unknown | null;
  thumbnail: unknown | null;
  output: unknown | null;
}

export async function fetchAnalysisFull(assistantId: string, token: string): Promise<AnalysisData> {
  const endpoints: [keyof AnalysisData, string][] = [
    ['nlp', `/api/analysis/${assistantId}/nlp`],
    ['llm', `/api/analysis/${assistantId}/llm`],
    ['deterministic', `/api/analysis/${assistantId}/deterministic`],
    ['insights', `/api/analysis/${assistantId}/insights`],
    ['thumbnail', `/api/analysis/${assistantId}/thumbnail`],
    ['output', `/api/analysis/${assistantId}/output`],
  ];

  const results = await Promise.allSettled(
    endpoints.map(([, url]) => apiFetch(url, { cache: 'no-store' }, token).then(r => r.ok ? r.json() : null))
  );

  const data: AnalysisData = { nlp: null, llm: null, deterministic: null, insights: null, thumbnail: null, output: null };
  endpoints.forEach(([key], i) => {
    const r = results[i];
    data[key] = r.status === 'fulfilled' ? r.value : null;
  });

  return data;
}

export async function regenerateScript(scriptId: string, feedback: string): Promise<{ success: boolean; error?: string }> {
  try {
    const r = await fetch(`/api/scripts/${scriptId}/regenerate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ feedback }),
    });
    if (!r.ok) return { success: false, error: await r.text() };
    return { success: true };
  } catch (e) {
    return { success: false, error: (e as Error).message };
  }
}

export async function fetchScriptVersions(scriptId: string): Promise<{ version: number; created_at: string }[]> {
  try {
    const r = await fetch(`/api/scripts/${scriptId}/versions`);
    const data = await r.json();
    return data.versions || [];
  } catch {
    return [];
  }
}
