'use client';

import { useState } from 'react';
import { Select } from '@/components/select';

// =============================================================================
// Types
// =============================================================================

interface CostEstimate {
  feature: string;
  provider: string;
  input_tokens?: number;
  output_tokens?: number;
  calls?: number;
  estimated_cost_usd: number;
  currency: string;
  breakdown: {
    provider: string;
    cost_usd: number;
    percentage: number;
  }[];
}

interface FeatureConfig {
  feature: string;
  providers: {
    id: string;
    name: string;
    input_cost_per_1k: number;
    output_cost_per_1k: number;
    flat_call_cost: number;
    min_cost: number;
  }[];
}

// =============================================================================
// Constants
// =============================================================================

const FEATURES: Record<string, string> = {
  transcript_extract: 'Transcript Extract',
  llm_text: 'LLM Text (Script Gen)',
  embedding: 'Embedding (RAG)',
  emotion_classifier: 'Emotion Classifier',
  tts: 'Text-to-Speech',
  thumbnail_vision: 'Thumbnail Vision',
};

const DEFAULT_CONFIGS: Record<string, FeatureConfig> = {
  transcript_extract: {
    feature: 'transcript_extract',
    providers: [
      { id: 'caption', name: 'YouTube Caption', input_cost_per_1k: 0, output_cost_per_1k: 0, flat_call_cost: 0, min_cost: 0 },
      { id: 'supadata', name: 'Supadata API', input_cost_per_1k: 0.001, output_cost_per_1k: 0, flat_call_cost: 0.01, min_cost: 0.01 },
      { id: 'whisper_groq', name: 'Whisper (Groq)', input_cost_per_1k: 0.006, output_cost_per_1k: 0, flat_call_cost: 0, min_cost: 0 },
      { id: 'whisper_openai', name: 'Whisper (OpenAI)', input_cost_per_1k: 0.006, output_cost_per_1k: 0, flat_call_cost: 0, min_cost: 0 },
    ],
  },
  llm_text: {
    feature: 'llm_text',
    providers: [
      { id: 'openai', name: 'OpenAI GPT-4o-mini', input_cost_per_1k: 0.00015, output_cost_per_1k: 0.0006, flat_call_cost: 0, min_cost: 0 },
      { id: 'gemini', name: 'Google Gemini 1.5 Flash', input_cost_per_1k: 0.000035, output_cost_per_1k: 0.00016, flat_call_cost: 0, min_cost: 0 },
      { id: 'groq', name: 'Groq Llama-3', input_cost_per_1k: 0.0001, output_cost_per_1k: 0.0001, flat_call_cost: 0, min_cost: 0 },
      { id: 'cohere', name: 'Cohere Command R+', input_cost_per_1k: 0.0005, output_cost_per_1k: 0.0015, flat_call_cost: 0, min_cost: 0 },
    ],
  },
  embedding: {
    feature: 'embedding',
    providers: [
      { id: 'openai_embed', name: 'OpenAI text-embedding-3-small', input_cost_per_1k: 0.00002, output_cost_per_1k: 0, flat_call_cost: 0, min_cost: 0 },
      { id: 'cohere_embed', name: 'Cohere Embed v3', input_cost_per_1k: 0.0001, output_cost_per_1k: 0, flat_call_cost: 0, min_cost: 0 },
    ],
  },
  tts: {
    feature: 'tts',
    providers: [
      { id: 'omnivoice', name: 'OmniVoice (Modal GPU)', input_cost_per_1k: 0, output_cost_per_1k: 0, flat_call_cost: 0.05, min_cost: 0.05 },
      { id: 'elevenlabs', name: 'ElevenLabs', input_cost_per_1k: 0, output_cost_per_1k: 0, flat_call_cost: 0.30, min_cost: 0.30 },
      { id: 'google_tts', name: 'Google Cloud TTS', input_cost_per_1k: 0, output_cost_per_1k: 0, flat_call_cost: 0.016, min_cost: 0.016 },
    ],
  },
};

// =============================================================================
// Main Page
// =============================================================================

export default function RoutingEstimatePage() {
  const [selectedFeature, setSelectedFeature] = useState<string>('llm_text');
  const [inputTokens, setInputTokens] = useState<number>(1000);
  const [outputTokens, setOutputTokens] = useState<number>(500);
  const [calls, setCalls] = useState<number>(1);
  const [estimate, setEstimate] = useState<CostEstimate | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const featureConfig = DEFAULT_CONFIGS[selectedFeature] || DEFAULT_CONFIGS.llm_text;

  async function handleEstimate() {
    setLoading(true);
    setError(null);
    
    try {
      // Call backend for real-time estimate
      const res = await fetch(
        `/api/admin/routing-config/${selectedFeature}/cost-estimate?input_tokens=${inputTokens}&output_tokens=${outputTokens}&calls=${calls}`
      );
      
      if (!res.ok) {
        throw new Error('Failed to fetch estimate');
      }
      
      const data = await res.json();
      setEstimate(data);
    } catch (err) {
      // Fallback: calculate locally
      const breakdown = featureConfig.providers.map(p => {
        const tokenCost = (inputTokens / 1000 * p.input_cost_per_1k) + 
                         (outputTokens / 1000 * p.output_cost_per_1k);
        const totalCost = Math.max(tokenCost * calls + p.flat_call_cost * calls, p.min_cost * calls);
        return {
          provider: p.id,
          cost_usd: totalCost,
          percentage: 0,
        };
      });
      
      const totalCost = breakdown.reduce((sum, b) => sum + b.cost_usd, 0);
      breakdown.forEach(b => {
        b.percentage = totalCost > 0 ? (b.cost_usd / totalCost) * 100 : 0;
      });
      
      setEstimate({
        feature: selectedFeature,
        provider: featureConfig.providers[0].id,
        input_tokens: inputTokens,
        output_tokens: outputTokens,
        calls: calls,
        estimated_cost_usd: totalCost,
        currency: 'USD',
        breakdown: breakdown,
      });
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="p-8 space-y-6 animate-fade-up">
      <div className="space-y-2">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-lg glass text-xs font-semibold text-[var(--brand-300)] uppercase tracking-wider">
          Admin
        </div>
        <h1 className="text-3xl lg:text-4xl font-bold tracking-tight">
          <span className="gradient-text">Cost Estimator</span>
        </h1>
        <p className="text-[var(--fg-secondary)]">
          Ước tính chi phí cho các service routing. Check real-time pricing từ routing config.
        </p>
      </div>

      <div className="grid lg:grid-cols-2 gap-6">
        {/* Input Form */}
        <div className="glass rounded-2xl p-6 space-y-5">
          <h2 className="text-lg font-semibold">Input Parameters</h2>

          {/* Feature Selection */}
          <div className="space-y-2">
            <label className="text-sm font-medium">Feature</label>
            <Select
              value={selectedFeature}
              onChange={(v) => {
                setSelectedFeature(v);
                setEstimate(null);
              }}
              options={Object.entries(FEATURES).map(([k, v]) => ({ value: k, label: v }))}
            />
          </div>

          {/* Token Inputs (for LLM/Embedding features) */}
          {(selectedFeature === 'llm_text' || selectedFeature === 'embedding') && (
            <>
              <div className="space-y-2">
                <label className="text-sm font-medium">
                  Input Tokens
                  <span className="ml-2 text-xs text-[var(--fg-tertiary)]">(characters / 4)</span>
                </label>
                <input
                  type="number"
                  value={inputTokens}
                  onChange={(e) => setInputTokens(Math.max(0, Number(e.target.value)))}
                  className="w-full px-4 py-2 rounded-lg bg-[var(--surface)] border border-[var(--glass-border)]"
                  min={0}
                  step={100}
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">
                  Output Tokens
                  <span className="ml-2 text-xs text-[var(--fg-tertiary)]">(estimated)</span>
                </label>
                <input
                  type="number"
                  value={outputTokens}
                  onChange={(e) => setOutputTokens(Math.max(0, Number(e.target.value)))}
                  className="w-full px-4 py-2 rounded-lg bg-[var(--surface)] border border-[var(--glass-border)]"
                  min={0}
                  step={100}
                />
              </div>
            </>
          )}

          {/* Number of Calls */}
          <div className="space-y-2">
            <label className="text-sm font-medium">Number of Calls</label>
            <input
              type="number"
              value={calls}
              onChange={(e) => setCalls(Math.max(1, Number(e.target.value)))}
              className="w-full px-4 py-2 rounded-lg bg-[var(--surface)] border border-[var(--glass-border)]"
              min={1}
              step={1}
            />
          </div>

          {/* Calculate Button */}
          <button
            onClick={handleEstimate}
            disabled={loading}
            className="w-full px-4 py-3 rounded-lg bg-[var(--brand-500)] text-white font-semibold disabled:opacity-50"
          >
            {loading ? 'Calculating…' : 'Calculate Cost Estimate'}
          </button>

          {error && (
            <div className="p-3 rounded-lg bg-red-500/20 text-red-400 text-sm">
              {error}
            </div>
          )}
        </div>

        {/* Results */}
        <div className="glass rounded-2xl p-6 space-y-5">
          <h2 className="text-lg font-semibold">Estimated Cost</h2>

          {estimate ? (
            <>
              {/* Total Cost */}
              <div className="p-6 rounded-xl bg-[var(--brand-500)]/10 border border-[var(--brand-500)]/30">
                <p className="text-sm text-[var(--fg-tertiary)]">Total Estimated Cost</p>
                <p className="text-4xl font-bold text-[var(--brand-300)]">
                  ${estimate.estimated_cost_usd.toFixed(4)}
                </p>
                <p className="text-xs text-[var(--fg-tertiary)] mt-1">
                  {estimate.calls} call{estimate.calls > 1 ? 's' : ''}
                  {estimate.input_tokens && ` · ${estimate.input_tokens.toLocaleString()} input tokens`}
                  {estimate.output_tokens && ` · ${estimate.output_tokens.toLocaleString()} output tokens`}
                </p>
              </div>

              {/* Breakdown by Provider */}
              <div className="space-y-3">
                <h3 className="text-sm font-semibold">Cost Breakdown by Provider</h3>
                {estimate.breakdown.map((b) => {
                  const providerInfo = featureConfig.providers.find(p => p.id === b.provider);
                  return (
                    <div key={b.provider} className="space-y-1">
                      <div className="flex justify-between text-sm">
                        <span>{providerInfo?.name || b.provider}</span>
                        <span className="font-mono">${b.cost_usd.toFixed(6)}</span>
                      </div>
                      <div className="h-2 rounded-full bg-[var(--surface)] overflow-hidden">
                        <div
                          className="h-full bg-[var(--brand-500)] rounded-full transition-all"
                          style={{ width: `${b.percentage}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Input Summary */}
              <div className="text-xs text-[var(--fg-tertiary)] space-y-1 bg-[var(--surface)] rounded-lg p-3">
                <p><strong>Feature:</strong> {FEATURES[estimate.feature] || estimate.feature}</p>
                <p><strong>Primary Provider:</strong> {estimate.provider}</p>
              </div>
            </>
          ) : (
            <div className="flex items-center justify-center h-48 text-[var(--fg-tertiary)]">
              Enter parameters and click Calculate
            </div>
          )}
        </div>
      </div>

      {/* Pricing Reference Table */}
      <div className="glass rounded-2xl p-6">
        <h2 className="text-lg font-semibold mb-4">Provider Pricing Reference</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-[var(--glass-border)]">
                <th className="px-4 py-2 text-left text-xs uppercase tracking-wider text-[var(--fg-tertiary)]">Provider</th>
                <th className="px-4 py-2 text-right text-xs uppercase tracking-wider text-[var(--fg-tertiary)]">Input ($/1K)</th>
                <th className="px-4 py-2 text-right text-xs uppercase tracking-wider text-[var(--fg-tertiary)]">Output ($/1K)</th>
                <th className="px-4 py-2 text-right text-xs uppercase tracking-wider text-[var(--fg-tertiary)]">Flat Call</th>
                <th className="px-4 py-2 text-right text-xs uppercase tracking-wider text-[var(--fg-tertiary)]">Min Cost</th>
              </tr>
            </thead>
            <tbody>
              {featureConfig.providers.map((p) => (
                <tr key={p.id} className="border-b border-[var(--glass-border)]">
                  <td className="px-4 py-2 font-medium">{p.name}</td>
                  <td className="px-4 py-2 text-right tabular-nums">${p.input_cost_per_1k.toFixed(6)}</td>
                  <td className="px-4 py-2 text-right tabular-nums">${p.output_cost_per_1k.toFixed(6)}</td>
                  <td className="px-4 py-2 text-right tabular-nums">${p.flat_call_cost.toFixed(4)}</td>
                  <td className="px-4 py-2 text-right tabular-nums">${p.min_cost.toFixed(4)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
